package api

import (
	"net/http"
	"strconv"

	"inventory-service/internal/models"
	"inventory-service/internal/service"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

type StockHandler struct {
	service service.InventoryService
	logger  *logrus.Logger
}

func NewStockHandler(service service.InventoryService, logger *logrus.Logger) *StockHandler {
	return &StockHandler{
		service: service,
		logger:  logger,
	}
}

func (h *StockHandler) CheckStock(c *gin.Context) {
	var request models.StockCheckRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Errorf("Invalid stock check request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}
	
	response, err := h.service.CheckStock(request.Items)
	if err != nil {
		h.logger.Errorf("Failed to check stock: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to check stock availability",
		})
		return
	}
	
	c.JSON(http.StatusOK, response)
}

func (h *StockHandler) ReserveStock(c *gin.Context) {
	var request models.ReserveStockRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Errorf("Invalid reserve stock request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}
	
	response, err := h.service.ReserveStock(request.OrderID, request.Items)
	if err != nil {
		h.logger.Errorf("Failed to reserve stock: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to reserve stock",
		})
		return
	}
	
	if response.Success {
		c.JSON(http.StatusOK, response)
	} else {
		c.JSON(http.StatusConflict, response)
	}
}

func (h *StockHandler) UpdateStock(c *gin.Context) {
	var request models.UpdateStockRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Errorf("Invalid update stock request: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}
	
	err := h.service.UpdateStock(request.SKU, request.Quantity, request.Type, "", request.Reason)
	if err != nil {
		h.logger.Errorf("Failed to update stock: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to update stock",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Stock updated successfully",
		"sku": request.SKU,
		"quantity": request.Quantity,
		"type": request.Type,
	})
}

type ReservationHandler struct {
	service service.InventoryService
	logger  *logrus.Logger
}

func NewReservationHandler(service service.InventoryService, logger *logrus.Logger) *ReservationHandler {
	return &ReservationHandler{
		service: service,
		logger:  logger,
	}
}

func (h *ReservationHandler) ConfirmReservation(c *gin.Context) {
	reservationIDStr := c.Param("id")
	reservationID, err := uuid.Parse(reservationIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid reservation ID format",
		})
		return
	}
	
	err = h.service.ConfirmReservation(reservationID)
	if err != nil {
		h.logger.Errorf("Failed to confirm reservation %s: %v", reservationID, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to confirm reservation",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Reservation confirmed successfully",
		"reservation_id": reservationID,
	})
}

func (h *ReservationHandler) ReleaseReservation(c *gin.Context) {
	reservationIDStr := c.Param("id")
	reservationID, err := uuid.Parse(reservationIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid reservation ID format",
		})
		return
	}
	
	err = h.service.ReleaseReservation(reservationID)
	if err != nil {
		h.logger.Errorf("Failed to release reservation %s: %v", reservationID, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to release reservation",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Reservation released successfully",
		"reservation_id": reservationID,
	})
}

func (h *ReservationHandler) GetReservation(c *gin.Context) {
	reservationIDStr := c.Param("id")
	reservationID, err := uuid.Parse(reservationIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid reservation ID format",
		})
		return
	}
	
	reservation, err := h.service.GetReservation(reservationID)
	if err != nil {
		h.logger.Errorf("Failed to get reservation %s: %v", reservationID, err)
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Reservation not found",
		})
		return
	}
	
	c.JSON(http.StatusOK, reservation)
}

func (h *ReservationHandler) GetReservationsByOrderID(c *gin.Context) {
	orderIDStr := c.Param("order_id")
	orderID, err := uuid.Parse(orderIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid order ID format",
		})
		return
	}
	
	reservations, err := h.service.GetReservationsByOrderID(orderID)
	if err != nil {
		h.logger.Errorf("Failed to get reservations for order %s: %v", orderID, err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to get reservations",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"order_id": orderID,
		"reservations": reservations,
	})
}

type InventoryHandler struct {
	service service.InventoryService
	logger  *logrus.Logger
}

func NewInventoryHandler(service service.InventoryService, logger *logrus.Logger) *InventoryHandler {
	return &InventoryHandler{
		service: service,
		logger:  logger,
	}
}

func (h *InventoryHandler) GetInventoryBySKU(c *gin.Context) {
	sku := c.Param("sku")
	if sku == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "SKU is required",
		})
		return
	}
	
	item, err := h.service.GetInventoryBySKU(sku)
	if err != nil {
		h.logger.Errorf("Failed to get inventory for SKU %s: %v", sku, err)
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Inventory item not found",
		})
		return
	}
	
	c.JSON(http.StatusOK, item)
}

func (h *InventoryHandler) GetInventoryByProductID(c *gin.Context) {
	productIDStr := c.Param("product_id")
	productID, err := uuid.Parse(productIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid product ID format",
		})
		return
	}
	
	item, err := h.service.GetInventoryByProductID(productID)
	if err != nil {
		h.logger.Errorf("Failed to get inventory for product %s: %v", productID, err)
		c.JSON(http.StatusNotFound, gin.H{
			"error": "Inventory item not found",
		})
		return
	}
	
	c.JSON(http.StatusOK, item)
}

func (h *InventoryHandler) SearchInventory(c *gin.Context) {
	query := c.Query("q")
	if query == "" {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Search query is required",
		})
		return
	}
	
	limitStr := c.DefaultQuery("limit", "50")
	offsetStr := c.DefaultQuery("offset", "0")
	
	limit, err := strconv.Atoi(limitStr)
	if err != nil || limit <= 0 {
		limit = 50
	}
	if limit > 100 {
		limit = 100 // Max limit
	}
	
	offset, err := strconv.Atoi(offsetStr)
	if err != nil || offset < 0 {
		offset = 0
	}
	
	items, err := h.service.SearchInventory(query, limit, offset)
	if err != nil {
		h.logger.Errorf("Failed to search inventory: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to search inventory",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"query": query,
		"limit": limit,
		"offset": offset,
		"results": items,
	})
}

func (h *InventoryHandler) GetLowStockItems(c *gin.Context) {
	items, err := h.service.GetLowStockItems()
	if err != nil {
		h.logger.Errorf("Failed to get low stock items: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to get low stock items",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"low_stock_items": items,
		"count": len(items),
	})
}

type AdminHandler struct {
	service service.InventoryService
	logger  *logrus.Logger
}

func NewAdminHandler(service service.InventoryService, logger *logrus.Logger) *AdminHandler {
	return &AdminHandler{
		service: service,
		logger:  logger,
	}
}

func (h *AdminHandler) ProcessExpiredReservations(c *gin.Context) {
	err := h.service.ProcessExpiredReservations()
	if err != nil {
		h.logger.Errorf("Failed to process expired reservations: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to process expired reservations",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Expired reservations processed successfully",
	})
}

func (h *AdminHandler) CleanupOldReservations(c *gin.Context) {
	err := h.service.CleanupOldReservations()
	if err != nil {
		h.logger.Errorf("Failed to cleanup old reservations: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to cleanup old reservations",
		})
		return
	}
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Old reservations cleaned up successfully",
	})
}
