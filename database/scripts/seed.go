package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"

	_ "github.com/lib/pq"
)

type InventorySeeder struct {
	db *sql.DB
}

func NewInventorySeeder() (*InventorySeeder, error) {
	dbHost := getEnv("DB_HOST", "localhost")
	dbPort := getEnv("DB_PORT", "5432")
	dbName := getEnv("DB_NAME", "aioutlet_inventory")
	dbUser := getEnv("DB_USER", "postgres")
	dbPassword := getEnv("DB_PASSWORD", "password")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, err
	}

	return &InventorySeeder{db: db}, nil
}

func (s *InventorySeeder) RunMigrations() error {
	log.Println("Running inventory service migrations...")

	migrationFiles := []string{
		"001_create_inventory_tables.sql",
		"002_add_inventory_extensions.sql",
	}

	for _, file := range migrationFiles {
		migrationPath := filepath.Join("..", "migrations", file)
		migrationBytes, err := ioutil.ReadFile(migrationPath)
		if err != nil {
			return fmt.Errorf("failed to read migration %s: %w", file, err)
		}

		log.Printf("Running migration: %s", file)
		_, err = s.db.Exec(string(migrationBytes))
		if err != nil {
			return fmt.Errorf("failed to execute migration %s: %w", file, err)
		}
	}

	return nil
}

func (s *InventorySeeder) SeedData() error {
	log.Println("Seeding inventory service data...")

	// Clear existing data
	if err := s.clearData(); err != nil {
		return err
	}

	// Seed in correct order (respecting foreign keys)
	if err := s.seedWarehouses(); err != nil {
		return err
	}

	if err := s.seedStockLevels(); err != nil {
		return err
	}

	log.Println("Inventory service data seeding completed successfully!")
	return nil
}

func (s *InventorySeeder) clearData() error {
	log.Println("Clearing existing inventory data...")

	clearQueries := []string{
		"DELETE FROM inventory.reservations;",
		"DELETE FROM inventory.alerts;",
		"DELETE FROM inventory.stock_movements;",
		"DELETE FROM inventory.stock_levels;",
		"DELETE FROM inventory.warehouses;",
	}

	for _, query := range clearQueries {
		_, err := s.db.Exec(query)
		if err != nil {
			return fmt.Errorf("failed to execute clear query %s: %w", query, err)
		}
		log.Printf("Executed: %s", query)
	}

	return nil
}

func (s *InventorySeeder) seedWarehouses() error {
	warehousesPath := filepath.Join("..", "seeds", "warehouses.json")
	warehousesBytes, err := ioutil.ReadFile(warehousesPath)
	if err != nil {
		return fmt.Errorf("failed to read warehouses.json: %w", err)
	}

	var warehouses []map[string]interface{}
	err = json.Unmarshal(warehousesBytes, &warehouses)
	if err != nil {
		return fmt.Errorf("failed to unmarshal warehouses: %w", err)
	}

	for _, warehouse := range warehouses {
		addressJSON, _ := json.Marshal(warehouse["address"])
		contactInfoJSON, _ := json.Marshal(warehouse["contact_info"])

		_, err = s.db.Exec(`
			INSERT INTO inventory.warehouses (
				id, name, code, address, contact_info, is_active, created_at, updated_at
			) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
		`, warehouse["id"], warehouse["name"], warehouse["code"],
			string(addressJSON), string(contactInfoJSON), warehouse["is_active"],
			warehouse["created_at"], warehouse["updated_at"])

		if err != nil {
			return fmt.Errorf("failed to insert warehouse: %w", err)
		}
	}

	log.Printf("Seeded %d warehouses", len(warehouses))
	return nil
}

func (s *InventorySeeder) seedStockLevels() error {
	stockPath := filepath.Join("..", "seeds", "stock_levels.json")
	stockBytes, err := ioutil.ReadFile(stockPath)
	if err != nil {
		return fmt.Errorf("failed to read stock_levels.json: %w", err)
	}

	var stockLevels []map[string]interface{}
	err = json.Unmarshal(stockBytes, &stockLevels)
	if err != nil {
		return fmt.Errorf("failed to unmarshal stock levels: %w", err)
	}

	for _, stock := range stockLevels {
		_, err = s.db.Exec(`
			INSERT INTO inventory.stock_levels (
				id, product_id, warehouse_id, sku, quantity_available,
				quantity_reserved, quantity_incoming, reorder_point,
				max_stock_level, cost_per_unit, last_restock_date,
				created_at, updated_at
			) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
		`, stock["id"], stock["product_id"], stock["warehouse_id"],
			stock["sku"], stock["quantity_available"], stock["quantity_reserved"],
			stock["quantity_incoming"], stock["reorder_point"],
			stock["max_stock_level"], stock["cost_per_unit"],
			stock["last_restock_date"], stock["created_at"], stock["updated_at"])

		if err != nil {
			return fmt.Errorf("failed to insert stock level: %w", err)
		}
	}

	log.Printf("Seeded %d stock levels", len(stockLevels))
	return nil
}

func (s *InventorySeeder) Close() error {
	return s.db.Close()
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func main() {
	seeder, err := NewInventorySeeder()
	if err != nil {
		log.Fatalf("Failed to create seeder: %v", err)
	}
	defer seeder.Close()

	if err := seeder.RunMigrations(); err != nil {
		log.Fatalf("Failed to run migrations: %v", err)
	}

	if err := seeder.SeedData(); err != nil {
		log.Fatalf("Failed to seed data: %v", err)
	}

	log.Println("Inventory database setup completed!")
}
