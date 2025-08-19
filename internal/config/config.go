package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	Environment      string
	LogLevel         int
	Server           ServerConfig
	Database         DatabaseConfig
	Redis            RedisConfig
	Security         SecurityConfig
	ExternalServices ExternalServicesConfig
	Inventory        InventoryConfig
	RateLimit        RateLimitConfig
	HealthCheck      HealthCheckConfig
	Metrics          MetricsConfig
	Logging          LoggingConfig
}

type ServerConfig struct {
	Port    int
	Host    string
	Mode    string // gin mode: debug, release, test
	Timeout int    // timeout in seconds
}

type DatabaseConfig struct {
	Host         string
	Port         int
	User         string
	Password     string
	Name         string
	SSLMode      string
	MaxPoolSize  int
	MaxIdleConns int
	MaxOpenConns int
}

type RedisConfig struct {
	Host       string
	Port       int
	Password   string
	DB         int
	KeyPrefix  string
	MaxRetries int
}

type SecurityConfig struct {
	JWTSecret   string
	JWTExpiresIn string
	JWTIssuer   string
	JWTAudience string
	CORSOrigins []string
	CORSMethods []string
	CORSHeaders []string
}

type ExternalServicesConfig struct {
	ProductServiceURL      string
	OrderServiceURL        string
	AuditServiceURL        string
	NotificationServiceURL string
}

type InventoryConfig struct {
	LowStockThreshold          int
	AutoReorderEnabled         bool
	AutoReorderQuantity        int
	StockReservationTimeout    int // minutes
	EnableStockTracking        bool
	EnableMultiWarehouse       bool
	DefaultWarehouse           string
	WarehouseLocations         []string
}

type RateLimitConfig struct {
	Enabled     bool
	PerMinute   int
	BurstLimit  int
}

type HealthCheckConfig struct {
	Enabled  bool
	Interval int    // seconds
	Endpoint string
}

type MetricsConfig struct {
	Enabled           bool
	Port              int
	PrometheusEnabled bool
}

type LoggingConfig struct {
	Level     string
	Format    string // json, text
	ToFile    bool
	ToConsole bool
	FilePath  string
}

// LoadConfig loads configuration based on environment
func LoadConfig() (*Config, error) {
	env := getEnv("ENVIRONMENT", "development")
	
	var config *Config
	
	switch env {
	case "development":
		devConfig := NewDevelopmentConfig()
		devConfig.OverrideWithEnv()
		config = devConfig.Config
	case "production":
		// TODO: Implement production config
		config = newDefaultConfig()
	case "testing":
		// TODO: Implement testing config  
		config = newDefaultConfig()
	default:
		config = newDefaultConfig()
	}
	
	return config, config.Validate()
}

// Validate validates the configuration
func (c *Config) Validate() error {
	if c.Server.Port <= 0 {
		return fmt.Errorf("server port must be positive")
	}
	
	if c.Database.Host == "" {
		return fmt.Errorf("database host is required")
	}
	
	if c.Database.Name == "" {
		return fmt.Errorf("database name is required")
	}
	
	return nil
}

// newDefaultConfig creates a default configuration
func newDefaultConfig() *Config {
	return &Config{
		Environment: "development",
		LogLevel:    4,
		Server: ServerConfig{
			Port:    8080,
			Host:    "0.0.0.0",
			Mode:    "release",
			Timeout: 30,
		},
		Database: DatabaseConfig{
			Host:         "localhost",
			Port:         5432,
			User:         "postgres",
			Password:     "password", 
			Name:         "inventory_db",
			SSLMode:      "disable",
			MaxPoolSize:  10,
			MaxIdleConns: 5,
			MaxOpenConns: 20,
		},
		Redis: RedisConfig{
			Host:       "localhost",
			Port:       6379,
			Password:   "",
			DB:         0,
			KeyPrefix:  "inventory:",
			MaxRetries: 3,
		},
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getEnvAsInt(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

func getEnvAsBool(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}

func getEnvAsDuration(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}
