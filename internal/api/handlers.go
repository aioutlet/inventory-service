package api

import (
	"net/http"
	"strconv"

	"inventory-service/internal/logger"
	"inventory-service/internal/models"
	"inventory-service/internal/service"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type StockHandler struct {
	service service.InventoryService
	logger  *logger.StandardLogger
}

func NewStockHandler(service service.InventoryService, logger *logger.StandardLogger) *StockHandler {
	return &StockHandler{
		service: service,
		logger:  logger,
	}
}

func (h *StockHandler) CheckStock(c *gin.Context) {
	startTime := h.logger.OperationStart("stock_check", c, map[string]interface{}{
		"operation": "stock_check",
	})
	
	var request models.StockCheckRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid stock check request", c, map[string]interface{}{
			"operation": "stock_check",
			"error": err.Error(),
		})
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}
	
	response, err := h.service.CheckStock(request.Items)
	if err != nil {
		h.logger.OperationFailed("stock_check", startTime, err, c, map[string]interface{}{
			"operation": "stock_check",
			"items_count": len(request.Items),
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to check stock availability",
		})
		return
	}
	
	h.logger.OperationComplete("stock_check", startTime, c, map[string]interface{}{
		"items_checked": len(request.Items),
		"available_items": len(response.Items),
	})
	c.JSON(http.StatusOK, response)
}

func (h *StockHandler) ReserveStock(c *gin.Context) {
	startTime := h.logger.OperationStart("stock_reserve", c, map[string]interface{}{
		"operation": "stock_reserve",
	})
	
	var request models.ReserveStockRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid reserve stock request", c, map[string]interface{}{
			"operation": "stock_reserve",
			"error": err.Error(),
		})
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}
	
	response, err := h.service.ReserveStock(request.OrderID, request.Items)
	if err != nil {
		h.logger.OperationFailed("stock_reserve", startTime, err, c, map[string]interface{}{
			"operation": "stock_reserve",
			"order_id": request.OrderID,
			"items_count": len(request.Items),
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to reserve stock",
		})
		return
	}
	
	if response.Success {
		h.logger.OperationComplete("stock_reserve", startTime, c, map[string]interface{}{
			"order_id": request.OrderID,
			"items_reserved": len(request.Items),
			"success": true,
		})
		c.JSON(http.StatusOK, response)
	} else {
		h.logger.Warn("Stock reservation failed - insufficient inventory", c, map[string]interface{}{
			"order_id": request.OrderID,
			"items_count": len(request.Items),
			"success": false,
		})
		c.JSON(http.StatusConflict, response)
	}
}

func (h *StockHandler) UpdateStock(c *gin.Context) {
	startTime := h.logger.OperationStart("stock_update", c, map[string]interface{}{
		"operation": "stock_update",
	})
	
	var request models.UpdateStockRequest
	if err := c.ShouldBindJSON(&request); err != nil {
		h.logger.Error("Invalid update stock request", c, map[string]interface{}{
			"operation": "stock_update",
			"error": err.Error(),
		})
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "Invalid request format",
			"details": err.Error(),
		})
		return
	}
	
	err := h.service.UpdateStock(request.SKU, request.Quantity, request.Type, "", request.Reason)
	if err != nil {
		h.logger.OperationFailed("stock_update", startTime, err, c, map[string]interface{}{
			"operation": "stock_update",
			"sku": request.SKU,
			"quantity": request.Quantity,
			"type": request.Type,
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to update stock",
		})
		return
	}
	
	h.logger.OperationComplete("stock_update", startTime, c, map[string]interface{}{
		"sku": request.SKU,
		"quantity": request.Quantity,
		"type": request.Type,
		"reason": request.Reason,
	})
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Stock updated successfully",
		"sku": request.SKU,
		"quantity": request.Quantity,
		"type": request.Type,
	})
}

type ReservationHandler struct {
	service service.InventoryService
	logger  *logger.StandardLogger
}

func NewReservationHandler(service service.InventoryService, logger *logger.StandardLogger) *ReservationHandler {
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
		h.logger.Error("Failed to confirm reservation", c, map[string]interface{}{
			"operation": "confirm_reservation",
			"reservation_id": reservationID,
			"error": err.Error(),
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to confirm reservation",
		})
		return
	}
	
	h.logger.Info("Reservation confirmed successfully", c, map[string]interface{}{
		"operation": "confirm_reservation",
		"reservation_id": reservationID,
	})
	
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
		h.logger.Error("Failed to release reservation", c, map[string]interface{}{
			"operation": "release_reservation",
			"reservation_id": reservationID,
			"error": err.Error(),
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to release reservation",
		})
		return
	}
	
	h.logger.Info("Reservation released successfully", c, map[string]interface{}{
		"operation": "release_reservation",
		"reservation_id": reservationID,
	})
	
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
		h.logger.Error("Failed to get reservation", c, map[string]interface{}{
			"operation": "get_reservation",
			"reservation_id": reservationID,
			"error": err.Error(),
		})
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
		h.logger.Error("Failed to get reservations for order", c, map[string]interface{}{
			"operation": "get_reservations_by_order",
			"order_id": orderID,
			"error": err.Error(),
		})
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
	logger  *logger.StandardLogger
}

func NewInventoryHandler(service service.InventoryService, logger *logger.StandardLogger) *InventoryHandler {
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
		h.logger.Error("Failed to get inventory for SKU", c, map[string]interface{}{
			"operation": "get_inventory_by_sku",
			"sku": sku,
			"error": err.Error(),
		})
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
		h.logger.Error("Failed to get inventory for product", c, map[string]interface{}{
			"operation": "get_inventory_by_product",
			"product_id": productID,
			"error": err.Error(),
		})
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
		h.logger.Error("Failed to search inventory", c, map[string]interface{}{
			"operation": "search_inventory",
			"query": query,
			"limit": limit,
			"offset": offset,
			"error": err.Error(),
		})
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
		h.logger.Error("Failed to get low stock items", c, map[string]interface{}{
			"operation": "get_low_stock_items",
			"error": err.Error(),
		})
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
	logger  *logger.StandardLogger
}

func NewAdminHandler(service service.InventoryService, logger *logger.StandardLogger) *AdminHandler {
	return &AdminHandler{
		service: service,
		logger:  logger,
	}
}

func (h *AdminHandler) ProcessExpiredReservations(c *gin.Context) {
	startTime := h.logger.OperationStart("process_expired_reservations", c, map[string]interface{}{
		"operation": "process_expired_reservations",
	})
	
	err := h.service.ProcessExpiredReservations()
	if err != nil {
		h.logger.OperationFailed("process_expired_reservations", startTime, err, c, map[string]interface{}{
			"operation": "process_expired_reservations",
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to process expired reservations",
		})
		return
	}
	
	h.logger.OperationComplete("process_expired_reservations", startTime, c, map[string]interface{}{
		"operation": "process_expired_reservations",
	})
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Expired reservations processed successfully",
	})
}

func (h *AdminHandler) CleanupOldReservations(c *gin.Context) {
	startTime := h.logger.OperationStart("cleanup_old_reservations", c, map[string]interface{}{
		"operation": "cleanup_old_reservations",
	})
	
	err := h.service.CleanupOldReservations()
	if err != nil {
		h.logger.OperationFailed("cleanup_old_reservations", startTime, err, c, map[string]interface{}{
			"operation": "cleanup_old_reservations",
		})
		c.JSON(http.StatusInternalServerError, gin.H{
			"error": "Failed to cleanup old reservations",
		})
		return
	}
	
	h.logger.OperationComplete("cleanup_old_reservations", startTime, c, map[string]interface{}{
		"operation": "cleanup_old_reservations",
	})
	
	c.JSON(http.StatusOK, gin.H{
		"message": "Old reservations cleaned up successfully",
	})
}
