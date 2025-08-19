package config

import (
	"fmt"
	"os"
	"strconv"
)

// DevelopmentConfig represents configuration for development environment
type DevelopmentConfig struct {
	*Config
}

// NewDevelopmentConfig creates a new development configuration
func NewDevelopmentConfig() *DevelopmentConfig {
	return &DevelopmentConfig{
		Config: &Config{
			Environment: "development",
			LogLevel:    4, // Debug level
			Server: ServerConfig{
				Port:    8080,
				Host:    "0.0.0.0",
				Mode:    "debug", // Gin debug mode
				Timeout: 30,
			},
			Database: DatabaseConfig{
				Host:        "localhost",
				Port:        5432,
				User:        "postgres",
				Password:    "password",
				Name:        "aioutlet_inventory_dev",
				SSLMode:     "disable",
				MaxPoolSize: 10,
				MaxIdleConns: 5,
				MaxOpenConns: 20,
			},
			Redis: RedisConfig{
				Host:       "localhost",
				Port:       6379,
				Password:   "",
				DB:         2,
				KeyPrefix:  "inventory:",
				MaxRetries: 3,
			},
			Security: SecurityConfig{
				JWTSecret:      "dev-jwt-secret-change-in-production",
				JWTExpiresIn:   "24h",
				JWTIssuer:      "ai-outlet-inventory-service",
				JWTAudience:    "ai-outlet-clients",
				CORSOrigins:    []string{"http://localhost:3000", "http://localhost:3001"},
				CORSMethods:    []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
				CORSHeaders:    []string{"Content-Type", "Authorization"},
			},
			ExternalServices: ExternalServicesConfig{
				ProductServiceURL:      "http://localhost:8000",
				OrderServiceURL:        "http://localhost:3005",
				AuditServiceURL:        "http://localhost:3009",
				NotificationServiceURL: "http://localhost:3008",
			},
			Inventory: InventoryConfig{
				LowStockThreshold:          10,
				AutoReorderEnabled:         true,
				AutoReorderQuantity:        100,
				StockReservationTimeout:    15,
				EnableStockTracking:        true,
				EnableMultiWarehouse:       false,
				DefaultWarehouse:           "main",
				WarehouseLocations:         []string{"main", "backup"},
			},
			RateLimit: RateLimitConfig{
				Enabled:     true,
				PerMinute:   1000,
				BurstLimit:  100,
			},
			HealthCheck: HealthCheckConfig{
				Enabled:  true,
				Interval: 30,
				Endpoint: "/health",
			},
			Metrics: MetricsConfig{
				Enabled:           true,
				Port:              9090,
				PrometheusEnabled: false, // Disable in development
			},
			Logging: LoggingConfig{
				Level:      "debug",
				Format:     "text", // text format for development
				ToFile:     false,
				ToConsole:  true,
				FilePath:   "logs/inventory-service-dev.log",
			},
		},
	}
}

// Validate validates the development configuration
func (c *DevelopmentConfig) Validate() error {
	// Add development-specific validation
	if c.Database.Name == "" {
		return fmt.Errorf("database name is required for development")
	}
	
	if c.Server.Port <= 0 {
		return fmt.Errorf("server port must be positive")
	}
	
	return c.Config.Validate()
}

// OverrideWithEnv allows environment variables to override configuration
func (c *DevelopmentConfig) OverrideWithEnv() {
	// Override with environment variables if they exist
	if env := os.Getenv("SERVER_PORT"); env != "" {
		if port, err := strconv.Atoi(env); err == nil {
			c.Server.Port = port
		}
	}
	
	if env := os.Getenv("GIN_MODE"); env != "" {
		c.Server.Mode = env
	}
	
	if env := os.Getenv("DB_HOST"); env != "" {
		c.Database.Host = env
	}
	
	if env := os.Getenv("DB_NAME"); env != "" {
		c.Database.Name = env
	}
	
	if env := os.Getenv("DB_USER"); env != "" {
		c.Database.User = env
	}
	
	if env := os.Getenv("DB_PASSWORD"); env != "" {
		c.Database.Password = env
	}
	
	if env := os.Getenv("REDIS_HOST"); env != "" {
		c.Redis.Host = env
	}
	
	if env := os.Getenv("JWT_SECRET"); env != "" {
		c.Security.JWTSecret = env
	}
}
