package main

import (
	"database/sql"
	"encoding/json"
	"flag"
	"log"
	"os"
	"time"

	"inventory-service/internal/config"
	"inventory-service/pkg/database"

	"github.com/google/uuid"
	_ "github.com/lib/pq"
)

type SampleProduct struct {
	SKU         string  `json:"sku"`
	Name        string  `json:"name"`
	Description string  `json:"description"`
	Price       float64 `json:"price"`
	Category    string  `json:"category"`
	Stock       int     `json:"stock"`
	ReorderLevel int    `json:"reorder_level"`
	MaxStock    int     `json:"max_stock"`
}

var sampleProducts = []SampleProduct{
	{
		SKU:         "LAPTOP-001",
		Name:        "MacBook Pro 16-inch",
		Description: "Apple MacBook Pro with M2 chip, 16GB RAM, 512GB SSD",
		Price:       2499.99,
		Category:    "Laptops",
		Stock:       25,
		ReorderLevel: 5,
		MaxStock:    100,
	},
	{
		SKU:         "LAPTOP-002",
		Name:        "Dell XPS 13",
		Description: "Dell XPS 13 with Intel i7, 16GB RAM, 256GB SSD",
		Price:       1299.99,
		Category:    "Laptops",
		Stock:       15,
		ReorderLevel: 3,
		MaxStock:    50,
	},
	{
		SKU:         "MOUSE-001",
		Name:        "Logitech MX Master 3",
		Description: "Advanced wireless mouse with ergonomic design",
		Price:       99.99,
		Category:    "Accessories",
		Stock:       150,
		ReorderLevel: 20,
		MaxStock:    300,
	},
	{
		SKU:         "KEYBOARD-001",
		Name:        "Apple Magic Keyboard",
		Description: "Wireless keyboard with numeric keypad",
		Price:       149.99,
		Category:    "Accessories",
		Stock:       75,
		ReorderLevel: 10,
		MaxStock:    200,
	},
	{
		SKU:         "MONITOR-001",
		Name:        "LG UltraWide 34-inch",
		Description: "34-inch curved ultrawide monitor with 4K resolution",
		Price:       599.99,
		Category:    "Monitors",
		Stock:       8,
		ReorderLevel: 2,
		MaxStock:    30,
	},
	{
		SKU:         "TABLET-001",
		Name:        "iPad Pro 12.9-inch",
		Description: "iPad Pro with M2 chip, 128GB storage, Wi-Fi",
		Price:       1099.99,
		Category:    "Tablets",
		Stock:       20,
		ReorderLevel: 5,
		MaxStock:    75,
	},
	{
		SKU:         "PHONE-001",
		Name:        "iPhone 15 Pro",
		Description: "iPhone 15 Pro 256GB in Natural Titanium",
		Price:       1199.99,
		Category:    "Smartphones",
		Stock:       30,
		ReorderLevel: 10,
		MaxStock:    100,
	},
	{
		SKU:         "HEADPHONES-001",
		Name:        "AirPods Pro (2nd Gen)",
		Description: "Active noise cancellation wireless earbuds",
		Price:       249.99,
		Category:    "Audio",
		Stock:       100,
		ReorderLevel: 15,
		MaxStock:    250,
	},
	{
		SKU:         "SPEAKER-001",
		Name:        "HomePod mini",
		Description: "Smart speaker with amazing sound and Siri",
		Price:       99.99,
		Category:    "Audio",
		Stock:       45,
		ReorderLevel: 8,
		MaxStock:    120,
	},
	{
		SKU:         "CAMERA-001",
		Name:        "Canon EOS R5",
		Description: "Full-frame mirrorless camera with 8K video",
		Price:       3899.99,
		Category:    "Cameras",
		Stock:       5,
		ReorderLevel: 1,
		MaxStock:    15,
	},
}

func main() {
	var (
		clearData = flag.Bool("clear", false, "Clear existing data before seeding")
		jsonFile  = flag.String("file", "", "JSON file with sample data")
	)
	flag.Parse()

	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Connect to database
	db, err := database.Connect(cfg.Database)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Load data from file if specified
	products := sampleProducts
	if *jsonFile != "" {
		products, err = loadProductsFromFile(*jsonFile)
		if err != nil {
			log.Fatalf("Failed to load products from file: %v", err)
		}
	}

	// Clear existing data if requested
	if *clearData {
		if err := clearExistingData(db); err != nil {
			log.Fatalf("Failed to clear existing data: %v", err)
		}
		log.Println("Cleared existing data")
	}

	// Seed data
	if err := seedProducts(db, products); err != nil {
		log.Fatalf("Failed to seed products: %v", err)
	}

	log.Printf("Successfully seeded %d products", len(products))
}

func loadProductsFromFile(filename string) ([]SampleProduct, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, err
	}

	var products []SampleProduct
	if err := json.Unmarshal(data, &products); err != nil {
		return nil, err
	}

	return products, nil
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
			return err
		}
	}

	return nil
}

func seedProducts(db *sql.DB, products []SampleProduct) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	// Prepare statements
	productStmt, err := tx.Prepare(`
		INSERT INTO products (id, sku, name, description, price, category, is_active)
		VALUES ($1, $2, $3, $4, $5, $6, $7)`)
	if err != nil {
		return err
	}
	defer productStmt.Close()

	inventoryStmt, err := tx.Prepare(`
		INSERT INTO inventory_items (product_id, sku, quantity_available, quantity_reserved, 
									reorder_level, max_stock, last_restocked)
		VALUES ($1, $2, $3, $4, $5, $6, $7)`)
	if err != nil {
		return err
	}
	defer inventoryStmt.Close()

	stockMovementStmt, err := tx.Prepare(`
		INSERT INTO stock_movements (product_id, sku, movement_type, quantity, reference, reason, created_by)
		VALUES ($1, $2, $3, $4, $5, $6, $7)`)
	if err != nil {
		return err
	}
	defer stockMovementStmt.Close()

	// Insert data
	for _, product := range products {
		productID := uuid.New()
		now := time.Now()

		// Insert product
		_, err := productStmt.Exec(
			productID,
			product.SKU,
			product.Name,
			product.Description,
			product.Price,
			product.Category,
			true,
		)
		if err != nil {
			return err
		}

		// Insert inventory item
		_, err = inventoryStmt.Exec(
			productID,
			product.SKU,
			product.Stock,
			0, // No reserved stock initially
			product.ReorderLevel,
			product.MaxStock,
			&now,
		)
		if err != nil {
			return err
		}

		// Insert initial stock movement
		_, err = stockMovementStmt.Exec(
			productID,
			product.SKU,
			"in",
			product.Stock,
			"SEED-DATA",
			"Initial stock from data seeding",
			"system",
		)
		if err != nil {
			return err
		}

		log.Printf("Seeded product: %s (%s) with %d units", product.Name, product.SKU, product.Stock)
	}

	return tx.Commit()
}
