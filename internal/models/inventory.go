package models

import (
	"time"

	"github.com/google/uuid"
)

type Product struct {
	ID          uuid.UUID `json:"id" db:"id"`
	SKU         string    `json:"sku" db:"sku"`
	Name        string    `json:"name" db:"name"`
	Description string    `json:"description" db:"description"`
	Price       float64   `json:"price" db:"price"`
	Category    string    `json:"category" db:"category"`
	IsActive    bool      `json:"is_active" db:"is_active"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

type InventoryItem struct {
	ID                uuid.UUID `json:"id" db:"id"`
	ProductID         uuid.UUID `json:"product_id" db:"product_id"`
	SKU               string    `json:"sku" db:"sku"`
	QuantityAvailable int       `json:"quantity_available" db:"quantity_available"`
	QuantityReserved  int       `json:"quantity_reserved" db:"quantity_reserved"`
	ReorderLevel      int       `json:"reorder_level" db:"reorder_level"`
	MaxStock          int       `json:"max_stock" db:"max_stock"`
	LastRestocked     *time.Time `json:"last_restocked" db:"last_restocked"`
	CreatedAt         time.Time `json:"created_at" db:"created_at"`
	UpdatedAt         time.Time `json:"updated_at" db:"updated_at"`
	Product           *Product  `json:"product,omitempty"`
}

type Reservation struct {
	ID           uuid.UUID         `json:"id" db:"id"`
	OrderID      uuid.UUID         `json:"order_id" db:"order_id"`
	ProductID    uuid.UUID         `json:"product_id" db:"product_id"`
	SKU          string            `json:"sku" db:"sku"`
	Quantity     int               `json:"quantity" db:"quantity"`
	Status       ReservationStatus `json:"status" db:"status"`
	ExpiresAt    time.Time         `json:"expires_at" db:"expires_at"`
	CreatedAt    time.Time         `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time         `json:"updated_at" db:"updated_at"`
	Product      *Product          `json:"product,omitempty"`
}

type ReservationStatus string

const (
	ReservationStatusPending   ReservationStatus = "pending"
	ReservationStatusConfirmed ReservationStatus = "confirmed"
	ReservationStatusReleased  ReservationStatus = "released"
	ReservationStatusExpired   ReservationStatus = "expired"
)

type StockMovement struct {
	ID          uuid.UUID        `json:"id" db:"id"`
	ProductID   uuid.UUID        `json:"product_id" db:"product_id"`
	SKU         string           `json:"sku" db:"sku"`
	MovementType StockMovementType `json:"movement_type" db:"movement_type"`
	Quantity    int              `json:"quantity" db:"quantity"`
	Reference   string           `json:"reference" db:"reference"` // Order ID, Restock ID, etc.
	Reason      string           `json:"reason" db:"reason"`
	CreatedAt   time.Time        `json:"created_at" db:"created_at"`
	CreatedBy   string           `json:"created_by" db:"created_by"`
}

type StockMovementType string

const (
	StockMovementTypeIn        StockMovementType = "in"        // Stock added
	StockMovementTypeOut       StockMovementType = "out"       // Stock removed
	StockMovementTypeReserved  StockMovementType = "reserved"  // Stock reserved
	StockMovementTypeReleased  StockMovementType = "released"  // Reservation released
	StockMovementTypeAdjustment StockMovementType = "adjustment" // Manual adjustment
)

// Request/Response DTOs
type StockCheckRequest struct {
	Items []StockCheckItem `json:"items" binding:"required"`
}

type StockCheckItem struct {
	SKU      string `json:"sku" binding:"required"`
	Quantity int    `json:"quantity" binding:"required,min=1"`
}

type StockCheckResponse struct {
	Available bool                    `json:"available"`
	Items     []StockCheckItemResult  `json:"items"`
}

type StockCheckItemResult struct {
	SKU               string `json:"sku"`
	RequestedQuantity int    `json:"requested_quantity"`
	AvailableQuantity int    `json:"available_quantity"`
	Available         bool   `json:"available"`
}

type ReserveStockRequest struct {
	OrderID uuid.UUID           `json:"order_id" binding:"required"`
	Items   []ReserveStockItem  `json:"items" binding:"required"`
}

type ReserveStockItem struct {
	SKU      string `json:"sku" binding:"required"`
	Quantity int    `json:"quantity" binding:"required,min=1"`
}

type ReserveStockResponse struct {
	ReservationID uuid.UUID `json:"reservation_id"`
	Success       bool      `json:"success"`
	ExpiresAt     time.Time `json:"expires_at"`
	Items         []ReservationItemResult `json:"items"`
}

type ReservationItemResult struct {
	SKU              string `json:"sku"`
	RequestedQuantity int   `json:"requested_quantity"`
	ReservedQuantity int    `json:"reserved_quantity"`
	Success          bool   `json:"success"`
}

type UpdateStockRequest struct {
	SKU      string            `json:"sku" binding:"required"`
	Quantity int               `json:"quantity" binding:"required"`
	Type     StockMovementType `json:"type" binding:"required"`
	Reason   string            `json:"reason" binding:"required"`
}
