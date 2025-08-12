package main

import (
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"time"

	"inventory-service/internal/config"
	"inventory-service/pkg/database"

	"github.com/google/uuid"
	_ "github.com/lib/pq"
)

type InventoryData struct {
	ProductID         string    `json:"product_id"`
	ProductSKU        string    `json:"product_sku"`
	ProductName       string    `json:"product_name"`
	Quantity          int       `json:"quantity"`
	ReservedQuantity  int       `json:"reserved_quantity"`
	MinStockLevel     int       `json:"min_stock_level"`
	MaxStockLevel     int       `json:"max_stock_level"`
	WarehouseLocation string    `json:"warehouse_location"`
	Supplier          string    `json:"supplier"`
	CostPrice         float64   `json:"cost_price"`
	LastRestocked     time.Time `json:"last_restocked"`
	Status            string    `json:"status"`
}

func main() {
	fmt.Println("🌱 AI Outlet - Inventory Service Data Seeder")
	fmt.Println("==================================================")

	var (
		clearData = flag.Bool("clear", false, "Clear existing data before seeding")
		jsonFile  = flag.String("file", "", "JSON file with inventory data")
		verbose   = flag.Bool("verbose", false, "Enable verbose logging")
		summary   = flag.Bool("summary", true, "Show summary after seeding")
	)
	flag.Parse()

	if *verbose {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
		log.Println("🔍 Verbose logging enabled")
	}

	// Load configuration
	log.Println("⚙️  Loading configuration...")
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("❌ Failed to load config: %v", err)
	}
	log.Println("✅ Configuration loaded successfully")

	// Connect to database
	log.Println("🔌 Connecting to database...")
	db, err := database.Connect(cfg.Database)
	if err != nil {
		log.Fatalf("❌ Failed to connect to database: %v", err)
	}
	defer db.Close()
	log.Println("✅ Database connected successfully")

	// Test database connection
	if err := db.Ping(); err != nil {
		log.Fatalf("❌ Database connection test failed: %v", err)
	}
	log.Println("✅ Database connection verified")

	// Determine which JSON file to use
	var dataFile string
	if *jsonFile != "" {
		dataFile = *jsonFile
		log.Printf("📁 Using specified file: %s", dataFile)
	} else {
		// Use default inventory data file
		dataFile = "scripts/inventory-data.json"
		log.Printf("📁 Using default file: %s", dataFile)
	}

	// Check if file exists
	if _, err := os.Stat(dataFile); os.IsNotExist(err) {
		log.Fatalf("❌ Data file not found: %s", dataFile)
	}

	// Load inventory data from JSON file
	log.Printf("� Loading inventory data from: %s", dataFile)
	inventoryItems, err := loadInventoryFromFile(dataFile)
	if err != nil {
		log.Fatalf("❌ Failed to load inventory data: %v", err)
	}
	log.Printf("✅ Loaded %d inventory items", len(inventoryItems))

	// Clear existing data if requested
	if *clearData {
		log.Println("🧹 Clearing existing data...")
		if err := clearExistingData(db); err != nil {
			log.Fatalf("❌ Failed to clear existing data: %v", err)
		}
		log.Println("✅ Existing data cleared successfully")
	}

	// Seed data
	log.Printf("🌱 Seeding %d inventory items...", len(inventoryItems))
	if err := seedInventoryData(db, inventoryItems, *verbose); err != nil {
		log.Fatalf("❌ Failed to seed inventory data: %v", err)
	}

	log.Printf("✅ Successfully seeded %d items", len(inventoryItems))

	if *summary {
		log.Println("📊 Database Summary:")
		printDatabaseSummary(db)
	}

	log.Println("🎉 Seeding completed successfully!")
}

func loadInventoryFromFile(filename string) ([]InventoryData, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var inventory []InventoryData
	if err := json.Unmarshal(data, &inventory); err != nil {
		return nil, err
	}

	return inventory, nil
}

func clearExistingData(db *sql.DB) error {
	queries := []string{
		"DELETE FROM stock_movements",
		"DELETE FROM reservations",
		"DELETE FROM inventory_items",
		"DELETE FROM products",
	}

	for _, query := range queries {
		if _, err := db.Exec(query); err != nil {
			log.Printf("⚠️  Warning: %v", err)
		}
	}

	return nil
}

func seedInventoryData(db *sql.DB, inventory []InventoryData, verbose bool) error {
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Prepare statements
	productStmt, err := tx.Prepare(`
		INSERT INTO products (id, sku, name, description, price, category, is_active)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (sku) DO UPDATE SET
		name = EXCLUDED.name,
		description = EXCLUDED.description,
		price = EXCLUDED.price,
		category = EXCLUDED.category`)
	if err != nil {
		return fmt.Errorf("failed to prepare product statement: %w", err)
	}
	defer productStmt.Close()

	inventoryStmt, err := tx.Prepare(`
		INSERT INTO inventory_items (product_id, sku, quantity_available, quantity_reserved, 
									reorder_level, max_stock, last_restocked)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		ON CONFLICT (sku) DO UPDATE SET
		quantity_available = EXCLUDED.quantity_available,
		quantity_reserved = EXCLUDED.quantity_reserved,
		reorder_level = EXCLUDED.reorder_level,
		max_stock = EXCLUDED.max_stock,
		last_restocked = EXCLUDED.last_restocked`)
	if err != nil {
		return fmt.Errorf("failed to prepare inventory statement: %w", err)
	}
	defer inventoryStmt.Close()

	stockMovementStmt, err := tx.Prepare(`
		INSERT INTO stock_movements (product_id, sku, movement_type, quantity, reference, reason, created_by)
		VALUES ($1, $2, $3, $4, $5, $6, $7)`)
	if err != nil {
		return fmt.Errorf("failed to prepare stock movement statement: %w", err)
	}
	defer stockMovementStmt.Close()

	// Insert data
	for i, item := range inventory {
		productID := uuid.New()

		// Calculate price from cost price (add 25% markup as example)
		price := item.CostPrice * 1.25

		// Insert/update product
		_, err := productStmt.Exec(
			productID,
			item.ProductSKU,
			item.ProductName,
			fmt.Sprintf("Inventory item: %s", item.ProductName),
			price,
			"General", // Default category
			true,
		)
		if err != nil {
			return fmt.Errorf("failed to insert product %s: %w", item.ProductSKU, err)
		}

		// Insert/update inventory item
		_, err = inventoryStmt.Exec(
			productID,
			item.ProductSKU,
			item.Quantity,
			item.ReservedQuantity,
			item.MinStockLevel,
			item.MaxStockLevel,
			item.LastRestocked,
		)
		if err != nil {
			return fmt.Errorf("failed to insert inventory for %s: %w", item.ProductSKU, err)
		}

		// Insert stock movement for available quantity
		if item.Quantity > 0 {
			_, err = stockMovementStmt.Exec(
				productID,
				item.ProductSKU,
				"in",
				item.Quantity,
				"SEED-DATA",
				fmt.Sprintf("Initial stock from data seeding - %s", item.Status),
				"system",
			)
			if err != nil {
				return fmt.Errorf("failed to insert stock movement for %s: %w", item.ProductSKU, err)
			}
		}

		if verbose {
			log.Printf("✓ [%d/%d] Seeded: %s (%s) - Qty: %d, Reserved: %d, Status: %s", 
				i+1, len(inventory), item.ProductName, item.ProductSKU, 
				item.Quantity, item.ReservedQuantity, item.Status)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %w", err)
	}

	return nil
}

func printDatabaseSummary(db *sql.DB) {
	// Count products
	var productCount int
	db.QueryRow("SELECT COUNT(*) FROM products").Scan(&productCount)
	log.Printf("   📦 Products: %d", productCount)

	// Count inventory items
	var inventoryCount int
	db.QueryRow("SELECT COUNT(*) FROM inventory_items").Scan(&inventoryCount)
	log.Printf("   📊 Inventory Items: %d", inventoryCount)

	// Count stock movements
	var movementCount int
	db.QueryRow("SELECT COUNT(*) FROM stock_movements").Scan(&movementCount)
	log.Printf("   📈 Stock Movements: %d", movementCount)

	// Total stock quantity
	var totalStock sql.NullInt64
	db.QueryRow("SELECT SUM(quantity_available) FROM inventory_items").Scan(&totalStock)
	if totalStock.Valid {
		log.Printf("   📋 Total Stock Quantity: %d", totalStock.Int64)
	}

	// Low stock items
	var lowStockCount int
	db.QueryRow("SELECT COUNT(*) FROM inventory_items WHERE quantity_available <= reorder_level").Scan(&lowStockCount)
	if lowStockCount > 0 {
		log.Printf("   ⚠️  Low Stock Items: %d", lowStockCount)
	}

	// Out of stock items
	var outOfStockCount int
	db.QueryRow("SELECT COUNT(*) FROM inventory_items WHERE quantity_available = 0").Scan(&outOfStockCount)
	if outOfStockCount > 0 {
		log.Printf("   ❌ Out of Stock Items: %d", outOfStockCount)
	}
}
