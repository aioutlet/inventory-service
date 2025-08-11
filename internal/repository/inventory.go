package repository

import (
	"database/sql"
	"fmt"
	"strings"

	"inventory-service/internal/models"

	"github.com/google/uuid"
)

type InventoryRepository interface {
	GetBySKU(sku string) (*models.InventoryItem, error)
	GetByProductID(productID uuid.UUID) (*models.InventoryItem, error)
	GetMultipleBySKUs(skus []string) ([]*models.InventoryItem, error)
	Create(item *models.InventoryItem) error
	Update(item *models.InventoryItem) error
	UpdateStock(sku string, quantityChange int, movementType models.StockMovementType, reference, reason string) error
	GetLowStockItems() ([]*models.InventoryItem, error)
	SearchInventory(query string, limit, offset int) ([]*models.InventoryItem, error)
}

type inventoryRepository struct {
	db *sql.DB
}

func NewInventoryRepository(db *sql.DB) InventoryRepository {
	return &inventoryRepository{db: db}
}

func (r *inventoryRepository) GetBySKU(sku string) (*models.InventoryItem, error) {
	query := `
		SELECT i.id, i.product_id, i.sku, i.quantity_available, i.quantity_reserved,
			   i.reorder_level, i.max_stock, i.last_restocked, i.created_at, i.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM inventory_items i
		JOIN products p ON i.product_id = p.id
		WHERE i.sku = $1`
	
	row := r.db.QueryRow(query, sku)
	
	item := &models.InventoryItem{Product: &models.Product{}}
	err := row.Scan(
		&item.ID, &item.ProductID, &item.SKU, &item.QuantityAvailable, &item.QuantityReserved,
		&item.ReorderLevel, &item.MaxStock, &item.LastRestocked, &item.CreatedAt, &item.UpdatedAt,
		&item.Product.ID, &item.Product.SKU, &item.Product.Name, &item.Product.Description,
		&item.Product.Price, &item.Product.Category, &item.Product.IsActive,
		&item.Product.CreatedAt, &item.Product.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("inventory item not found for SKU: %s", sku)
		}
		return nil, fmt.Errorf("failed to get inventory item: %w", err)
	}
	
	return item, nil
}

func (r *inventoryRepository) GetByProductID(productID uuid.UUID) (*models.InventoryItem, error) {
	query := `
		SELECT i.id, i.product_id, i.sku, i.quantity_available, i.quantity_reserved,
			   i.reorder_level, i.max_stock, i.last_restocked, i.created_at, i.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM inventory_items i
		JOIN products p ON i.product_id = p.id
		WHERE i.product_id = $1`
	
	row := r.db.QueryRow(query, productID)
	
	item := &models.InventoryItem{Product: &models.Product{}}
	err := row.Scan(
		&item.ID, &item.ProductID, &item.SKU, &item.QuantityAvailable, &item.QuantityReserved,
		&item.ReorderLevel, &item.MaxStock, &item.LastRestocked, &item.CreatedAt, &item.UpdatedAt,
		&item.Product.ID, &item.Product.SKU, &item.Product.Name, &item.Product.Description,
		&item.Product.Price, &item.Product.Category, &item.Product.IsActive,
		&item.Product.CreatedAt, &item.Product.UpdatedAt,
	)
	
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("inventory item not found for product ID: %s", productID)
		}
		return nil, fmt.Errorf("failed to get inventory item: %w", err)
	}
	
	return item, nil
}

func (r *inventoryRepository) GetMultipleBySKUs(skus []string) ([]*models.InventoryItem, error) {
	if len(skus) == 0 {
		return []*models.InventoryItem{}, nil
	}
	
	placeholders := make([]string, len(skus))
	args := make([]interface{}, len(skus))
	for i, sku := range skus {
		placeholders[i] = fmt.Sprintf("$%d", i+1)
		args[i] = sku
	}
	
	query := fmt.Sprintf(`
		SELECT i.id, i.product_id, i.sku, i.quantity_available, i.quantity_reserved,
			   i.reorder_level, i.max_stock, i.last_restocked, i.created_at, i.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM inventory_items i
		JOIN products p ON i.product_id = p.id
		WHERE i.sku IN (%s)`, strings.Join(placeholders, ","))
	
	rows, err := r.db.Query(query, args...)
	if err != nil {
		return nil, fmt.Errorf("failed to query inventory items: %w", err)
	}
	defer rows.Close()
	
	var items []*models.InventoryItem
	for rows.Next() {
		item := &models.InventoryItem{Product: &models.Product{}}
		err := rows.Scan(
			&item.ID, &item.ProductID, &item.SKU, &item.QuantityAvailable, &item.QuantityReserved,
			&item.ReorderLevel, &item.MaxStock, &item.LastRestocked, &item.CreatedAt, &item.UpdatedAt,
			&item.Product.ID, &item.Product.SKU, &item.Product.Name, &item.Product.Description,
			&item.Product.Price, &item.Product.Category, &item.Product.IsActive,
			&item.Product.CreatedAt, &item.Product.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan inventory item: %w", err)
		}
		items = append(items, item)
	}
	
	return items, nil
}

func (r *inventoryRepository) Create(item *models.InventoryItem) error {
	query := `
		INSERT INTO inventory_items (product_id, sku, quantity_available, quantity_reserved,
									reorder_level, max_stock, last_restocked)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
		RETURNING id, created_at, updated_at`
	
	err := r.db.QueryRow(query, item.ProductID, item.SKU, item.QuantityAvailable,
		item.QuantityReserved, item.ReorderLevel, item.MaxStock, item.LastRestocked).
		Scan(&item.ID, &item.CreatedAt, &item.UpdatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to create inventory item: %w", err)
	}
	
	return nil
}

func (r *inventoryRepository) Update(item *models.InventoryItem) error {
	query := `
		UPDATE inventory_items 
		SET quantity_available = $1, quantity_reserved = $2, reorder_level = $3,
			max_stock = $4, last_restocked = $5
		WHERE id = $6
		RETURNING updated_at`
	
	err := r.db.QueryRow(query, item.QuantityAvailable, item.QuantityReserved,
		item.ReorderLevel, item.MaxStock, item.LastRestocked, item.ID).
		Scan(&item.UpdatedAt)
	
	if err != nil {
		return fmt.Errorf("failed to update inventory item: %w", err)
	}
	
	return nil
}

func (r *inventoryRepository) UpdateStock(sku string, quantityChange int, movementType models.StockMovementType, reference, reason string) error {
	tx, err := r.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()
	
	// Get current inventory item
	var item models.InventoryItem
	query := `SELECT id, product_id, quantity_available, quantity_reserved FROM inventory_items WHERE sku = $1 FOR UPDATE`
	err = tx.QueryRow(query, sku).Scan(&item.ID, &item.ProductID, &item.QuantityAvailable, &item.QuantityReserved)
	if err != nil {
		return fmt.Errorf("failed to get inventory item for update: %w", err)
	}
	
	// Update quantities based on movement type
	switch movementType {
	case models.StockMovementTypeIn:
		item.QuantityAvailable += quantityChange
	case models.StockMovementTypeOut:
		item.QuantityAvailable -= quantityChange
	case models.StockMovementTypeReserved:
		item.QuantityAvailable -= quantityChange
		item.QuantityReserved += quantityChange
	case models.StockMovementTypeReleased:
		item.QuantityAvailable += quantityChange
		item.QuantityReserved -= quantityChange
	case models.StockMovementTypeAdjustment:
		item.QuantityAvailable = quantityChange // Set to absolute value for adjustments
	}
	
	// Validate quantities
	if item.QuantityAvailable < 0 || item.QuantityReserved < 0 {
		return fmt.Errorf("insufficient stock: available=%d, reserved=%d", item.QuantityAvailable, item.QuantityReserved)
	}
	
	// Update inventory
	updateQuery := `UPDATE inventory_items SET quantity_available = $1, quantity_reserved = $2 WHERE id = $3`
	_, err = tx.Exec(updateQuery, item.QuantityAvailable, item.QuantityReserved, item.ID)
	if err != nil {
		return fmt.Errorf("failed to update inventory: %w", err)
	}
	
	// Record stock movement
	movementQuery := `
		INSERT INTO stock_movements (product_id, sku, movement_type, quantity, reference, reason)
		VALUES ($1, $2, $3, $4, $5, $6)`
	_, err = tx.Exec(movementQuery, item.ProductID, sku, movementType, quantityChange, reference, reason)
	if err != nil {
		return fmt.Errorf("failed to record stock movement: %w", err)
	}
	
	return tx.Commit()
}

func (r *inventoryRepository) GetLowStockItems() ([]*models.InventoryItem, error) {
	query := `
		SELECT i.id, i.product_id, i.sku, i.quantity_available, i.quantity_reserved,
			   i.reorder_level, i.max_stock, i.last_restocked, i.created_at, i.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM inventory_items i
		JOIN products p ON i.product_id = p.id
		WHERE i.quantity_available <= i.reorder_level AND p.is_active = true
		ORDER BY i.quantity_available ASC`
	
	rows, err := r.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to get low stock items: %w", err)
	}
	defer rows.Close()
	
	var items []*models.InventoryItem
	for rows.Next() {
		item := &models.InventoryItem{Product: &models.Product{}}
		err := rows.Scan(
			&item.ID, &item.ProductID, &item.SKU, &item.QuantityAvailable, &item.QuantityReserved,
			&item.ReorderLevel, &item.MaxStock, &item.LastRestocked, &item.CreatedAt, &item.UpdatedAt,
			&item.Product.ID, &item.Product.SKU, &item.Product.Name, &item.Product.Description,
			&item.Product.Price, &item.Product.Category, &item.Product.IsActive,
			&item.Product.CreatedAt, &item.Product.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan low stock item: %w", err)
		}
		items = append(items, item)
	}
	
	return items, nil
}

func (r *inventoryRepository) SearchInventory(query string, limit, offset int) ([]*models.InventoryItem, error) {
	searchQuery := `
		SELECT i.id, i.product_id, i.sku, i.quantity_available, i.quantity_reserved,
			   i.reorder_level, i.max_stock, i.last_restocked, i.created_at, i.updated_at,
			   p.id, p.sku, p.name, p.description, p.price, p.category, p.is_active,
			   p.created_at, p.updated_at
		FROM inventory_items i
		JOIN products p ON i.product_id = p.id
		WHERE (p.name ILIKE $1 OR p.sku ILIKE $1 OR p.category ILIKE $1)
		ORDER BY p.name
		LIMIT $2 OFFSET $3`
	
	searchPattern := "%" + query + "%"
	rows, err := r.db.Query(searchQuery, searchPattern, limit, offset)
	if err != nil {
		return nil, fmt.Errorf("failed to search inventory: %w", err)
	}
	defer rows.Close()
	
	var items []*models.InventoryItem
	for rows.Next() {
		item := &models.InventoryItem{Product: &models.Product{}}
		err := rows.Scan(
			&item.ID, &item.ProductID, &item.SKU, &item.QuantityAvailable, &item.QuantityReserved,
			&item.ReorderLevel, &item.MaxStock, &item.LastRestocked, &item.CreatedAt, &item.UpdatedAt,
			&item.Product.ID, &item.Product.SKU, &item.Product.Name, &item.Product.Description,
			&item.Product.Price, &item.Product.Category, &item.Product.IsActive,
			&item.Product.CreatedAt, &item.Product.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan inventory item: %w", err)
		}
		items = append(items, item)
	}
	
	return items, nil
}
