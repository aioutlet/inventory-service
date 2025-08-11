package service

import (
	"testing"
	"time"

	"inventory-service/internal/models"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

// Mock repositories
type MockInventoryRepository struct {
	mock.Mock
}

func (m *MockInventoryRepository) GetBySKU(sku string) (*models.InventoryItem, error) {
	args := m.Called(sku)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.InventoryItem), args.Error(1)
}

func (m *MockInventoryRepository) GetByProductID(productID uuid.UUID) (*models.InventoryItem, error) {
	args := m.Called(productID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.InventoryItem), args.Error(1)
}

func (m *MockInventoryRepository) GetMultipleBySKUs(skus []string) ([]*models.InventoryItem, error) {
	args := m.Called(skus)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.InventoryItem), args.Error(1)
}

func (m *MockInventoryRepository) Create(item *models.InventoryItem) error {
	args := m.Called(item)
	return args.Error(0)
}

func (m *MockInventoryRepository) Update(item *models.InventoryItem) error {
	args := m.Called(item)
	return args.Error(0)
}

func (m *MockInventoryRepository) UpdateStock(sku string, quantityChange int, movementType models.StockMovementType, reference, reason string) error {
	args := m.Called(sku, quantityChange, movementType, reference, reason)
	return args.Error(0)
}

func (m *MockInventoryRepository) GetLowStockItems() ([]*models.InventoryItem, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.InventoryItem), args.Error(1)
}

func (m *MockInventoryRepository) SearchInventory(query string, limit, offset int) ([]*models.InventoryItem, error) {
	args := m.Called(query, limit, offset)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.InventoryItem), args.Error(1)
}

type MockReservationRepository struct {
	mock.Mock
}

func (m *MockReservationRepository) Create(reservation *models.Reservation) error {
	args := m.Called(reservation)
	if args.Get(0) != nil {
		reservation.ID = args.Get(0).(uuid.UUID)
	}
	return args.Error(1)
}

func (m *MockReservationRepository) GetByID(id uuid.UUID) (*models.Reservation, error) {
	args := m.Called(id)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).(*models.Reservation), args.Error(1)
}

func (m *MockReservationRepository) GetByOrderID(orderID uuid.UUID) ([]*models.Reservation, error) {
	args := m.Called(orderID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Reservation), args.Error(1)
}

func (m *MockReservationRepository) UpdateStatus(id uuid.UUID, status models.ReservationStatus) error {
	args := m.Called(id, status)
	return args.Error(0)
}

func (m *MockReservationRepository) GetExpiredReservations() ([]*models.Reservation, error) {
	args := m.Called()
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Reservation), args.Error(1)
}

func (m *MockReservationRepository) DeleteExpired(expiredBefore time.Time) error {
	args := m.Called(expiredBefore)
	return args.Error(0)
}

func (m *MockReservationRepository) GetActiveReservationsForProduct(productID uuid.UUID) ([]*models.Reservation, error) {
	args := m.Called(productID)
	if args.Get(0) == nil {
		return nil, args.Error(1)
	}
	return args.Get(0).([]*models.Reservation), args.Error(1)
}

func TestInventoryService_CheckStock(t *testing.T) {
	tests := []struct {
		name           string
		items          []models.StockCheckItem
		inventoryItems []*models.InventoryItem
		expectedResult *models.StockCheckResponse
		expectError    bool
	}{
		{
			name: "All items available",
			items: []models.StockCheckItem{
				{SKU: "SKU001", Quantity: 5},
				{SKU: "SKU002", Quantity: 3},
			},
			inventoryItems: []*models.InventoryItem{
				{SKU: "SKU001", QuantityAvailable: 10},
				{SKU: "SKU002", QuantityAvailable: 5},
			},
			expectedResult: &models.StockCheckResponse{
				Available: true,
				Items: []models.StockCheckItemResult{
					{SKU: "SKU001", RequestedQuantity: 5, AvailableQuantity: 10, Available: true},
					{SKU: "SKU002", RequestedQuantity: 3, AvailableQuantity: 5, Available: true},
				},
			},
			expectError: false,
		},
		{
			name: "Insufficient stock",
			items: []models.StockCheckItem{
				{SKU: "SKU001", Quantity: 15},
				{SKU: "SKU002", Quantity: 3},
			},
			inventoryItems: []*models.InventoryItem{
				{SKU: "SKU001", QuantityAvailable: 10},
				{SKU: "SKU002", QuantityAvailable: 5},
			},
			expectedResult: &models.StockCheckResponse{
				Available: false,
				Items: []models.StockCheckItemResult{
					{SKU: "SKU001", RequestedQuantity: 15, AvailableQuantity: 10, Available: false},
					{SKU: "SKU002", RequestedQuantity: 3, AvailableQuantity: 5, Available: true},
				},
			},
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup mocks
			mockInventoryRepo := new(MockInventoryRepository)
			mockReservationRepo := new(MockReservationRepository)
			
			// Extract SKUs for mock call
			skus := make([]string, len(tt.items))
			for i, item := range tt.items {
				skus[i] = item.SKU
			}
			
			mockInventoryRepo.On("GetMultipleBySKUs", skus).Return(tt.inventoryItems, nil)
			
			// Create service (without Redis for simplicity in tests)
			service := &inventoryService{
				inventoryRepo:   mockInventoryRepo,
				reservationRepo: mockReservationRepo,
			}
			
			// Execute
			result, err := service.CheckStock(tt.items)
			
			// Assert
			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, result)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.Equal(t, tt.expectedResult.Available, result.Available)
				assert.Len(t, result.Items, len(tt.expectedResult.Items))
				
				for i, expectedItem := range tt.expectedResult.Items {
					assert.Equal(t, expectedItem.SKU, result.Items[i].SKU)
					assert.Equal(t, expectedItem.RequestedQuantity, result.Items[i].RequestedQuantity)
					assert.Equal(t, expectedItem.AvailableQuantity, result.Items[i].AvailableQuantity)
					assert.Equal(t, expectedItem.Available, result.Items[i].Available)
				}
			}
			
			mockInventoryRepo.AssertExpectations(t)
		})
	}
}

func TestInventoryService_ReserveStock(t *testing.T) {
	orderID := uuid.New()
	productID := uuid.New()
	
	tests := []struct {
		name           string
		orderID        uuid.UUID
		items          []models.ReserveStockItem
		inventoryItems []*models.InventoryItem
		expectSuccess  bool
		expectError    bool
	}{
		{
			name:    "Successful reservation",
			orderID: orderID,
			items: []models.ReserveStockItem{
				{SKU: "SKU001", Quantity: 5},
			},
			inventoryItems: []*models.InventoryItem{
				{SKU: "SKU001", ProductID: productID, QuantityAvailable: 10},
			},
			expectSuccess: true,
			expectError:   false,
		},
		{
			name:    "Insufficient stock",
			orderID: orderID,
			items: []models.ReserveStockItem{
				{SKU: "SKU001", Quantity: 15},
			},
			inventoryItems: []*models.InventoryItem{
				{SKU: "SKU001", ProductID: productID, QuantityAvailable: 10},
			},
			expectSuccess: false,
			expectError:   false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Setup mocks
			mockInventoryRepo := new(MockInventoryRepository)
			mockReservationRepo := new(MockReservationRepository)
			
			// Mock stock check
			skus := make([]string, len(tt.items))
			for i, item := range tt.items {
				skus[i] = item.SKU
			}
			mockInventoryRepo.On("GetMultipleBySKUs", skus).Return(tt.inventoryItems, nil)
			
			if tt.expectSuccess {
				// Mock successful reservation creation and stock update
				for _, item := range tt.items {
					mockInventoryRepo.On("GetBySKU", item.SKU).Return(tt.inventoryItems[0], nil)
					mockReservationRepo.On("Create", mock.AnythingOfType("*models.Reservation")).Return(uuid.New(), nil)
					mockInventoryRepo.On("UpdateStock", item.SKU, item.Quantity, models.StockMovementTypeReserved, mock.AnythingOfType("string"), mock.AnythingOfType("string")).Return(nil)
				}
			}
			
			// Create service
			service := &inventoryService{
				inventoryRepo:   mockInventoryRepo,
				reservationRepo: mockReservationRepo,
			}
			
			// Execute
			result, err := service.ReserveStock(tt.orderID, tt.items)
			
			// Assert
			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, result)
				assert.Equal(t, tt.expectSuccess, result.Success)
				
				if tt.expectSuccess {
					assert.NotEqual(t, uuid.Nil, result.ReservationID)
					assert.NotZero(t, result.ExpiresAt)
				}
			}
			
			mockInventoryRepo.AssertExpectations(t)
			mockReservationRepo.AssertExpectations(t)
		})
	}
}
