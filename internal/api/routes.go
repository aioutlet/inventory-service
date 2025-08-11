package api

import (
	"net/http"

	"inventory-service/internal/service"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

func SetupRoutes(router *gin.Engine, inventoryService service.InventoryService, logger *logrus.Logger) {
	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status": "healthy",
			"service": "inventory-service",
		})
	})
	
	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		// Stock management
		v1.POST("/stock/check", NewStockHandler(inventoryService, logger).CheckStock)
		v1.POST("/stock/reserve", NewStockHandler(inventoryService, logger).ReserveStock)
		v1.PUT("/stock/update", NewStockHandler(inventoryService, logger).UpdateStock)
		
		// Reservation management
		v1.PUT("/reservations/:id/confirm", NewReservationHandler(inventoryService, logger).ConfirmReservation)
		v1.PUT("/reservations/:id/release", NewReservationHandler(inventoryService, logger).ReleaseReservation)
		v1.GET("/reservations/:id", NewReservationHandler(inventoryService, logger).GetReservation)
		v1.GET("/orders/:order_id/reservations", NewReservationHandler(inventoryService, logger).GetReservationsByOrderID)
		
		// Inventory queries
		v1.GET("/inventory/sku/:sku", NewInventoryHandler(inventoryService, logger).GetInventoryBySKU)
		v1.GET("/inventory/product/:product_id", NewInventoryHandler(inventoryService, logger).GetInventoryByProductID)
		v1.GET("/inventory/search", NewInventoryHandler(inventoryService, logger).SearchInventory)
		v1.GET("/inventory/low-stock", NewInventoryHandler(inventoryService, logger).GetLowStockItems)
		
		// Admin endpoints
		admin := v1.Group("/admin")
		{
			admin.POST("/reservations/process-expired", NewAdminHandler(inventoryService, logger).ProcessExpiredReservations)
			admin.DELETE("/reservations/cleanup", NewAdminHandler(inventoryService, logger).CleanupOldReservations)
		}
	}
}
