package api

import (
	"inventory-service/internal/logger"
	"inventory-service/internal/service"

	"github.com/gin-gonic/gin"
)

func SetupRoutes(router *gin.Engine, inventoryService service.InventoryService, standardLogger *logger.StandardLogger) {
	// Operational endpoints for infrastructure/monitoring
	operationalController := NewOperationalController()
	router.GET("/health", operationalController.Health)
	router.GET("/health/ready", operationalController.Readiness)
	router.GET("/health/live", operationalController.Liveness)
	router.GET("/metrics", operationalController.Metrics)
	
	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		// Stock management
		v1.POST("/stock/check", NewStockHandler(inventoryService, standardLogger).CheckStock)
		v1.POST("/stock/reserve", NewStockHandler(inventoryService, standardLogger).ReserveStock)
		v1.PUT("/stock/update", NewStockHandler(inventoryService, standardLogger).UpdateStock)
		
		// Reservation management
		v1.PUT("/reservations/:id/confirm", NewReservationHandler(inventoryService, standardLogger).ConfirmReservation)
		v1.PUT("/reservations/:id/release", NewReservationHandler(inventoryService, standardLogger).ReleaseReservation)
		v1.GET("/reservations/:id", NewReservationHandler(inventoryService, standardLogger).GetReservation)
		v1.GET("/orders/:order_id/reservations", NewReservationHandler(inventoryService, standardLogger).GetReservationsByOrderID)
		
		// Inventory queries
		v1.GET("/inventory/sku/:sku", NewInventoryHandler(inventoryService, standardLogger).GetInventoryBySKU)
		v1.GET("/inventory/product/:product_id", NewInventoryHandler(inventoryService, standardLogger).GetInventoryByProductID)
		v1.GET("/inventory/search", NewInventoryHandler(inventoryService, standardLogger).SearchInventory)
		v1.GET("/inventory/low-stock", NewInventoryHandler(inventoryService, standardLogger).GetLowStockItems)
		
		// Admin endpoints
		admin := v1.Group("/admin")
		{
			admin.POST("/reservations/process-expired", NewAdminHandler(inventoryService, standardLogger).ProcessExpiredReservations)
			admin.DELETE("/reservations/cleanup", NewAdminHandler(inventoryService, standardLogger).CleanupOldReservations)
		}
	}
}
