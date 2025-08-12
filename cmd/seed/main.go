package main

import (
	"database/sql"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"time"

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

// Standalone database connection
func connectDB() (*sql.DB, error) {
	// Use environment variables or default values
	host := getEnv("DB_HOST", "localhost")
	port := getEnv("DB_PORT", "5432")
	user := getEnv("DB_USER", "inventory_user")
	password := getEnv("DB_PASSWORD", "inventory_pass")
	dbname := getEnv("DB_NAME", "inventory_db")
	sslmode := getEnv("DB_SSL_MODE", "disable")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=%s",
		host, port, user, password, dbname, sslmode)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		return nil, fmt.Errorf("failed to open database connection: %w", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	return db, nil
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func loadInventoryData(filename string) ([]InventoryData, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to open file %s: %w", filename, err)
	}
	defer file.Close()

	var inventory []InventoryData
	decoder := json.NewDecoder(file)
	if err := decoder.Decode(&inventory); err != nil {
		return nil, fmt.Errorf("failed to decode JSON: %w", err)
	}

	return inventory, nil
}

func seedInventoryData(db *sql.DB, inventory []InventoryData, verbose bool) error {
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Prepare statement for inventory items only (no products table)
	inventoryStmt, err := tx.Prepare(`
		INSERT INTO inventory_items (
			id, product_id, sku, quantity_available, quantity_reserved, 
			reorder_level, max_stock, warehouse_location, supplier, 
			cost_price, last_restocked, status
		)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
		ON CONFLICT (sku) DO UPDATE SET
		product_id = EXCLUDED.product_id,
		quantity_available = EXCLUDED.quantity_available,
		quantity_reserved = EXCLUDED.quantity_reserved,
		reorder_level = EXCLUDED.reorder_level,
		max_stock = EXCLUDED.max_stock,
		warehouse_location = EXCLUDED.warehouse_location,
		supplier = EXCLUDED.supplier,
		cost_price = EXCLUDED.cost_price,
		last_restocked = EXCLUDED.last_restocked,
		status = EXCLUDED.status`)
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
		inventoryID := uuid.New()

		// Insert/update inventory item (no product table needed)
		_, err := inventoryStmt.Exec(
			inventoryID,
			item.ProductID,        // MongoDB ObjectId as string
			item.ProductSKU,
			item.Quantity,
			item.ReservedQuantity,
			item.MinStockLevel,
			item.MaxStockLevel,
			item.WarehouseLocation,
			item.Supplier,
			item.CostPrice,
			item.LastRestocked,
			item.Status,
		)
		if err != nil {
			return fmt.Errorf("failed to insert inventory for %s: %w", item.ProductSKU, err)
		}

		// Insert stock movement for available quantity
		if item.Quantity > 0 {
			_, err = stockMovementStmt.Exec(
				item.ProductID,  // MongoDB ObjectId
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

func clearExistingData(db *sql.DB, verbose bool) error {
	if verbose {
		log.Println("🧹 Clearing existing data...")
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Clear in order to respect foreign key constraints
	tables := []string{"stock_movements", "reservations", "inventory_items"}
	
	for _, table := range tables {
		_, err := tx.Exec(fmt.Sprintf("DELETE FROM %s", table))
		if err != nil {
			return fmt.Errorf("failed to clear table %s: %w", table, err)
		}
		if verbose {
			log.Printf("   ✓ Cleared table: %s", table)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit clear transaction: %w", err)
	}

	return nil
}

func main() {
	fmt.Println("🌱 AI Outlet - Inventory Service Data Seeder (Standalone)")
	fmt.Println("=========================================================")

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

	// Connect to database
	db, err := connectDB()
	if err != nil {
		log.Fatalf("❌ Database connection failed: %v", err)
	}
	defer db.Close()

	if *verbose {
		log.Println("✅ Database connection established")
	}

	// Clear data if requested
	if *clearData {
		if err := clearExistingData(db, *verbose); err != nil {
			log.Fatalf("❌ Failed to clear existing data: %v", err)
		}
		fmt.Println("🧹 Existing data cleared successfully")
	}

	// Determine data source
	var inventory []InventoryData
	if *jsonFile != "" {
		if *verbose {
			log.Printf("📂 Loading data from file: %s", *jsonFile)
		}
		inventory, err = loadInventoryData(*jsonFile)
		if err != nil {
			log.Fatalf("❌ Failed to load data from file: %v", err)
		}
	} else {
		// Default to scripts/inventory-data.json
		defaultFile := "scripts/inventory-data.json"
		if *verbose {
			log.Printf("📂 Loading data from default file: %s", defaultFile)
		}
		inventory, err = loadInventoryData(defaultFile)
		if err != nil {
			log.Fatalf("❌ Failed to load data from default file: %v", err)
		}
	}

	if len(inventory) == 0 {
		log.Fatalf("❌ No inventory data found to seed")
	}

	if *verbose {
		log.Printf("📦 Found %d inventory items to seed", len(inventory))
	}

	// Seed the data
	fmt.Printf("🌱 Seeding %d inventory items...\n", len(inventory))
	if err := seedInventoryData(db, inventory, *verbose); err != nil {
		log.Fatalf("❌ Failed to seed inventory data: %v", err)
	}

	fmt.Println("✅ Inventory data seeded successfully!")

	// Show summary if requested
	if *summary {
		var totalItems, totalStock int
		err := db.QueryRow("SELECT COUNT(*), COALESCE(SUM(quantity_available), 0) FROM inventory_items").Scan(&totalItems, &totalStock)
		if err != nil {
			log.Printf("⚠️  Failed to get summary: %v", err)
		} else {
			fmt.Printf("\n📊 Summary:\n")
			fmt.Printf("   • Total inventory items: %d\n", totalItems)
			fmt.Printf("   • Total stock quantity: %d\n", totalStock)
		}
	}

	fmt.Println("\n🎉 Seeding completed successfully!")
}
