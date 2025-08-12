package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"inventory-service/internal/api"
	"inventory-service/internal/config"
	"inventory-service/internal/logger"
	"inventory-service/internal/middleware"
	"inventory-service/internal/repository"
	"inventory-service/internal/service"
	"inventory-service/pkg/database"
	"inventory-service/pkg/redis"

	"github.com/gin-gonic/gin"
)

func main() {
	// Load configuration
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("Failed to load config: %v", err)
	}

	// Setup logger
	standardLogger := logger.NewStandardLogger()

	// Initialize database
	db, err := database.Connect(cfg.Database)
	if err != nil {
		standardLogger.Fatal("Failed to connect to database", nil, map[string]interface{}{
			"error": err.Error(),
		})
	}
	defer db.Close()

	// Run migrations
	if err := database.Migrate(cfg.Database); err != nil {
		standardLogger.Fatal("Failed to run migrations", nil, map[string]interface{}{
			"error": err.Error(),
		})
	}

	// Initialize Redis
	redisClient, err := redis.Connect(cfg.Redis)
	if err != nil {
		standardLogger.Fatal("Failed to connect to Redis", nil, map[string]interface{}{
			"error": err.Error(),
		})
	}
	defer redisClient.Close()

	// Initialize repositories
	inventoryRepo := repository.NewInventoryRepository(db)
	reservationRepo := repository.NewReservationRepository(db)

	// Initialize services
	inventoryService := service.NewInventoryService(inventoryRepo, reservationRepo, redisClient, standardLogger)

	// Initialize HTTP server
	if cfg.Environment == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(middleware.CorrelationIDMiddleware()) // Add correlation ID middleware
	
	// Custom logging middleware
	router.Use(func(c *gin.Context) {
		start := time.Now()
		c.Next()
		
		duration := time.Since(start).Milliseconds()
		
		standardLogger.Info("HTTP request", c, map[string]interface{}{
			"method":     c.Request.Method,
			"path":       c.Request.URL.Path,
			"status":     c.Writer.Status(),
			"duration":   duration,
			"ip":         c.ClientIP(),
			"userAgent":  c.Request.UserAgent(),
		})
	})

	// Setup routes
	api.SetupRoutes(router, inventoryService, standardLogger)

	// Create server
	srv := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Server.Port),
		Handler: router,
	}

	// Start server in goroutine
	go func() {
		standardLogger.Info("Starting server", nil, map[string]interface{}{
			"port": cfg.Server.Port,
		})
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			standardLogger.Fatal("Failed to start server", nil, map[string]interface{}{
				"error": err.Error(),
			})
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit
	standardLogger.Info("Shutting down server", nil, nil)

	// Graceful shutdown
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	
	if err := srv.Shutdown(ctx); err != nil {
		standardLogger.Fatal("Server forced to shutdown", nil, map[string]interface{}{
			"error": err.Error(),
		})
	}

	standardLogger.Info("Server exited", nil, nil)
}
