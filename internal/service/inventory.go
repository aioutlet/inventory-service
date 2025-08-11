package service

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"inventory-service/internal/models"
	"inventory-service/internal/repository"

	"github.com/google/uuid"
	"github.com/redis/go-redis/v9"
	"github.com/sirupsen/logrus"
)

type InventoryService interface {
	// Stock Management
	CheckStock(items []models.StockCheckItem) (*models.StockCheckResponse, error)
	ReserveStock(orderID uuid.UUID, items []models.ReserveStockItem) (*models.ReserveStockResponse, error)
	ConfirmReservation(reservationID uuid.UUID) error
	ReleaseReservation(reservationID uuid.UUID) error
	UpdateStock(sku string, quantity int, movementType models.StockMovementType, reference, reason string) error
	
	// Inventory Queries
	GetInventoryBySKU(sku string) (*models.InventoryItem, error)
	GetInventoryByProductID(productID uuid.UUID) (*models.InventoryItem, error)
	SearchInventory(query string, limit, offset int) ([]*models.InventoryItem, error)
	GetLowStockItems() ([]*models.InventoryItem, error)
	
	// Reservation Management
	GetReservation(reservationID uuid.UUID) (*models.Reservation, error)
	GetReservationsByOrderID(orderID uuid.UUID) ([]*models.Reservation, error)
	
	// Background Tasks
	ProcessExpiredReservations() error
	CleanupOldReservations() error
}

type inventoryService struct {
	inventoryRepo   repository.InventoryRepository
	reservationRepo repository.ReservationRepository
	redis          *redis.Client
	logger         *logrus.Logger
}

func NewInventoryService(
	inventoryRepo repository.InventoryRepository,
	reservationRepo repository.ReservationRepository,
	redis *redis.Client,
	logger *logrus.Logger,
) InventoryService {
	return &inventoryService{
		inventoryRepo:   inventoryRepo,
		reservationRepo: reservationRepo,
		redis:          redis,
		logger:         logger,
	}
}

func (s *inventoryService) CheckStock(items []models.StockCheckItem) (*models.StockCheckResponse, error) {
	skus := make([]string, len(items))
	for i, item := range items {
		skus[i] = item.SKU
	}
	
	// Try to get from cache first
	cacheKey := fmt.Sprintf("stock_check:%v", skus)
	cached, err := s.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var response models.StockCheckResponse
		if json.Unmarshal([]byte(cached), &response) == nil {
			s.logger.Debug("Stock check served from cache")
			return &response, nil
		}
	}
	
	// Get inventory items from database
	inventoryItems, err := s.inventoryRepo.GetMultipleBySKUs(skus)
	if err != nil {
		return nil, fmt.Errorf("failed to get inventory items: %w", err)
	}
	
	// Create a map for quick lookup
	inventoryMap := make(map[string]*models.InventoryItem)
	for _, item := range inventoryItems {
		inventoryMap[item.SKU] = item
	}
	
	// Check availability for each requested item
	response := &models.StockCheckResponse{
		Available: true,
		Items:     make([]models.StockCheckItemResult, len(items)),
	}
	
	for i, requestedItem := range items {
		result := models.StockCheckItemResult{
			SKU:               requestedItem.SKU,
			RequestedQuantity: requestedItem.Quantity,
			AvailableQuantity: 0,
			Available:         false,
		}
		
		if inventoryItem, exists := inventoryMap[requestedItem.SKU]; exists {
			result.AvailableQuantity = inventoryItem.QuantityAvailable
			result.Available = inventoryItem.QuantityAvailable >= requestedItem.Quantity
		}
		
		if !result.Available {
			response.Available = false
		}
		
		response.Items[i] = result
	}
	
	// Cache the result for 30 seconds
	responseJSON, _ := json.Marshal(response)
	s.redis.Set(context.Background(), cacheKey, responseJSON, 30*time.Second)
	
	return response, nil
}

func (s *inventoryService) ReserveStock(orderID uuid.UUID, items []models.ReserveStockItem) (*models.ReserveStockResponse, error) {
	// First check if we have enough stock
	stockCheckItems := make([]models.StockCheckItem, len(items))
	for i, item := range items {
		stockCheckItems[i] = models.StockCheckItem{
			SKU:      item.SKU,
			Quantity: item.Quantity,
		}
	}
	
	stockCheck, err := s.CheckStock(stockCheckItems)
	if err != nil {
		return nil, fmt.Errorf("failed to check stock: %w", err)
	}
	
	if !stockCheck.Available {
		return &models.ReserveStockResponse{
			Success: false,
			Items:   []models.ReservationItemResult{},
		}, nil
	}
	
	// Create reservations
	reservationID := uuid.New()
	expiresAt := time.Now().Add(15 * time.Minute) // 15 minute reservation window
	
	response := &models.ReserveStockResponse{
		ReservationID: reservationID,
		Success:       true,
		ExpiresAt:     expiresAt,
		Items:         make([]models.ReservationItemResult, len(items)),
	}
	
	for i, item := range items {
		// Get product info
		inventoryItem, err := s.inventoryRepo.GetBySKU(item.SKU)
		if err != nil {
			s.logger.Errorf("Failed to get inventory item for SKU %s: %v", item.SKU, err)
			response.Success = false
			continue
		}
		
		// Create reservation
		reservation := &models.Reservation{
			OrderID:   orderID,
			ProductID: inventoryItem.ProductID,
			SKU:       item.SKU,
			Quantity:  item.Quantity,
			Status:    models.ReservationStatusPending,
			ExpiresAt: expiresAt,
		}
		
		err = s.reservationRepo.Create(reservation)
		if err != nil {
			s.logger.Errorf("Failed to create reservation for SKU %s: %v", item.SKU, err)
			response.Success = false
			continue
		}
		
		// Update inventory (reserve stock)
		err = s.inventoryRepo.UpdateStock(item.SKU, item.Quantity, models.StockMovementTypeReserved, 
			orderID.String(), fmt.Sprintf("Stock reserved for order %s", orderID))
		if err != nil {
			s.logger.Errorf("Failed to reserve stock for SKU %s: %v", item.SKU, err)
			response.Success = false
			continue
		}
		
		response.Items[i] = models.ReservationItemResult{
			SKU:              item.SKU,
			RequestedQuantity: item.Quantity,
			ReservedQuantity:  item.Quantity,
			Success:          true,
		}
		
		s.logger.Infof("Reserved %d units of SKU %s for order %s", item.Quantity, item.SKU, orderID)
	}
	
	// Invalidate cache
	s.invalidateStockCache()
	
	return response, nil
}

func (s *inventoryService) ConfirmReservation(reservationID uuid.UUID) error {
	reservation, err := s.reservationRepo.GetByID(reservationID)
	if err != nil {
		return fmt.Errorf("failed to get reservation: %w", err)
	}
	
	if reservation.Status != models.ReservationStatusPending {
		return fmt.Errorf("reservation is not pending: %s", reservation.Status)
	}
	
	if reservation.ExpiresAt.Before(time.Now()) {
		return fmt.Errorf("reservation has expired")
	}
	
	err = s.reservationRepo.UpdateStatus(reservationID, models.ReservationStatusConfirmed)
	if err != nil {
		return fmt.Errorf("failed to confirm reservation: %w", err)
	}
	
	s.logger.Infof("Confirmed reservation %s for order %s", reservationID, reservation.OrderID)
	return nil
}

func (s *inventoryService) ReleaseReservation(reservationID uuid.UUID) error {
	reservation, err := s.reservationRepo.GetByID(reservationID)
	if err != nil {
		return fmt.Errorf("failed to get reservation: %w", err)
	}
	
	if reservation.Status == models.ReservationStatusReleased {
		return nil // Already released
	}
	
	// Release the stock back to available inventory
	err = s.inventoryRepo.UpdateStock(reservation.SKU, reservation.Quantity, models.StockMovementTypeReleased,
		reservation.OrderID.String(), fmt.Sprintf("Reservation %s released", reservationID))
	if err != nil {
		return fmt.Errorf("failed to release stock: %w", err)
	}
	
	// Update reservation status
	err = s.reservationRepo.UpdateStatus(reservationID, models.ReservationStatusReleased)
	if err != nil {
		return fmt.Errorf("failed to update reservation status: %w", err)
	}
	
	// Invalidate cache
	s.invalidateStockCache()
	
	s.logger.Infof("Released reservation %s for order %s", reservationID, reservation.OrderID)
	return nil
}

func (s *inventoryService) UpdateStock(sku string, quantity int, movementType models.StockMovementType, reference, reason string) error {
	err := s.inventoryRepo.UpdateStock(sku, quantity, movementType, reference, reason)
	if err != nil {
		return fmt.Errorf("failed to update stock: %w", err)
	}
	
	// Invalidate cache
	s.invalidateStockCache()
	
	s.logger.Infof("Updated stock for SKU %s: %s %d units (reason: %s)", sku, movementType, quantity, reason)
	return nil
}

func (s *inventoryService) GetInventoryBySKU(sku string) (*models.InventoryItem, error) {
	// Try cache first
	cacheKey := fmt.Sprintf("inventory:%s", sku)
	cached, err := s.redis.Get(context.Background(), cacheKey).Result()
	if err == nil {
		var item models.InventoryItem
		if json.Unmarshal([]byte(cached), &item) == nil {
			return &item, nil
		}
	}
	
	item, err := s.inventoryRepo.GetBySKU(sku)
	if err != nil {
		return nil, err
	}
	
	// Cache for 5 minutes
	itemJSON, _ := json.Marshal(item)
	s.redis.Set(context.Background(), cacheKey, itemJSON, 5*time.Minute)
	
	return item, nil
}

func (s *inventoryService) GetInventoryByProductID(productID uuid.UUID) (*models.InventoryItem, error) {
	return s.inventoryRepo.GetByProductID(productID)
}

func (s *inventoryService) SearchInventory(query string, limit, offset int) ([]*models.InventoryItem, error) {
	return s.inventoryRepo.SearchInventory(query, limit, offset)
}

func (s *inventoryService) GetLowStockItems() ([]*models.InventoryItem, error) {
	return s.inventoryRepo.GetLowStockItems()
}

func (s *inventoryService) GetReservation(reservationID uuid.UUID) (*models.Reservation, error) {
	return s.reservationRepo.GetByID(reservationID)
}

func (s *inventoryService) GetReservationsByOrderID(orderID uuid.UUID) ([]*models.Reservation, error) {
	return s.reservationRepo.GetByOrderID(orderID)
}

func (s *inventoryService) ProcessExpiredReservations() error {
	expiredReservations, err := s.reservationRepo.GetExpiredReservations()
	if err != nil {
		return fmt.Errorf("failed to get expired reservations: %w", err)
	}
	
	for _, reservation := range expiredReservations {
		// Release the stock
		err = s.inventoryRepo.UpdateStock(reservation.SKU, reservation.Quantity, models.StockMovementTypeReleased,
			reservation.OrderID.String(), fmt.Sprintf("Expired reservation %s", reservation.ID))
		if err != nil {
			s.logger.Errorf("Failed to release stock for expired reservation %s: %v", reservation.ID, err)
			continue
		}
		
		// Mark as expired
		err = s.reservationRepo.UpdateStatus(reservation.ID, models.ReservationStatusExpired)
		if err != nil {
			s.logger.Errorf("Failed to mark reservation %s as expired: %v", reservation.ID, err)
			continue
		}
		
		s.logger.Infof("Processed expired reservation %s for order %s", reservation.ID, reservation.OrderID)
	}
	
	if len(expiredReservations) > 0 {
		s.invalidateStockCache()
	}
	
	return nil
}

func (s *inventoryService) CleanupOldReservations() error {
	// Delete reservations that expired more than 24 hours ago
	cutoff := time.Now().Add(-24 * time.Hour)
	return s.reservationRepo.DeleteExpired(cutoff)
}

func (s *inventoryService) invalidateStockCache() {
	// Delete all stock-related cache keys
	ctx := context.Background()
	keys, err := s.redis.Keys(ctx, "stock_check:*").Result()
	if err == nil && len(keys) > 0 {
		s.redis.Del(ctx, keys...)
	}
	
	keys, err = s.redis.Keys(ctx, "inventory:*").Result()
	if err == nil && len(keys) > 0 {
		s.redis.Del(ctx, keys...)
	}
}
