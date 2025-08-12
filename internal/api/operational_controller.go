package api

import (
	"net/http"
	"os"
	"runtime"
	"time"

	"github.com/gin-gonic/gin"
)

var startTime = time.Now()

// OperationalController handles operational/infrastructure endpoints
type OperationalController struct{}

// NewOperationalController creates a new operational controller
func NewOperationalController() *OperationalController {
	return &OperationalController{}
}

// Health basic health check endpoint
func (oc *OperationalController) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":    "healthy",
		"service":   "inventory-service",
		"timestamp": time.Now().Format(time.RFC3339),
		"version":   getEnvOrDefault("API_VERSION", "1.0.0"),
	})
}

// Readiness readiness probe - check if service is ready to serve traffic
func (oc *OperationalController) Readiness(c *gin.Context) {
	// Add more sophisticated checks here (DB connectivity, Redis, external dependencies, etc.)
	// Example: Check database connectivity, Redis connectivity, etc.
	
	c.JSON(http.StatusOK, gin.H{
		"status":    "ready",
		"service":   "inventory-service",
		"timestamp": time.Now().Format(time.RFC3339),
		"checks": gin.H{
			"database": "connected",
			"redis":    "connected",
			// Add other dependency checks
		},
	})
}

// Liveness liveness probe - check if the app is running
func (oc *OperationalController) Liveness(c *gin.Context) {
	uptime := time.Since(startTime).Seconds()
	
	c.JSON(http.StatusOK, gin.H{
		"status":    "alive",
		"service":   "inventory-service",
		"timestamp": time.Now().Format(time.RFC3339),
		"uptime":    uptime,
	})
}

// Metrics basic metrics endpoint
func (oc *OperationalController) Metrics(c *gin.Context) {
	var m runtime.MemStats
	runtime.ReadMemStats(&m)
	
	uptime := time.Since(startTime).Seconds()
	
	c.JSON(http.StatusOK, gin.H{
		"service":   "inventory-service",
		"timestamp": time.Now().Format(time.RFC3339),
		"metrics": gin.H{
			"uptime": uptime,
			"memory": gin.H{
				"alloc":      m.Alloc,
				"total_alloc": m.TotalAlloc,
				"sys":        m.Sys,
				"heap_alloc": m.HeapAlloc,
				"heap_sys":   m.HeapSys,
			},
			"goroutines":   runtime.NumGoroutine(),
			"go_version":   runtime.Version(),
			"go_os":        runtime.GOOS,
			"go_arch":      runtime.GOARCH,
		},
	})
}

// Helper function to get environment variable with default
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
