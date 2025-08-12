package logger

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"
	"time"

	"inventory-service/internal/middleware"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// LogLevel represents the log levels
type LogLevel int

const (
	DebugLevel LogLevel = iota
	InfoLevel
	WarnLevel
	ErrorLevel
	FatalLevel
)

// StandardLogger provides enhanced logging with correlation ID and metadata support
type StandardLogger struct {
	logger      *logrus.Logger
	serviceName string
}

// LogEntry represents a structured log entry
type LogEntry struct {
	Timestamp     time.Time              `json:"timestamp"`
	Level         string                 `json:"level"`
	Service       string                 `json:"service"`
	CorrelationID string                 `json:"correlationId,omitempty"`
	Message       string                 `json:"message"`
	UserID        string                 `json:"userId,omitempty"`
	Operation     string                 `json:"operation,omitempty"`
	Duration      int64                  `json:"duration,omitempty"`
	Metadata      map[string]interface{} `json:"metadata,omitempty"`
}

// NewStandardLogger creates a new standardized logger
func NewStandardLogger() *StandardLogger {
	// Environment-based configuration
	environment := getEnv("ENVIRONMENT", "development")
	isDevelopment := environment == "development"
	isProduction := environment == "production"
	
	serviceName := getEnv("SERVICE_NAME", "inventory-service")
	logLevel := getEnv("LOG_LEVEL", func() string {
		if isDevelopment {
			return "debug"
		}
		return "info"
	}())
	logFormat := getEnv("LOG_FORMAT", func() string {
		if isProduction {
			return "json"
		}
		return "console"
	}())
	
	logger := logrus.New()
	
	// Set log level
	switch strings.ToLower(logLevel) {
	case "debug":
		logger.SetLevel(logrus.DebugLevel)
	case "info":
		logger.SetLevel(logrus.InfoLevel)
	case "warn":
		logger.SetLevel(logrus.WarnLevel)
	case "error":
		logger.SetLevel(logrus.ErrorLevel)
	case "fatal":
		logger.SetLevel(logrus.FatalLevel)
	default:
		logger.SetLevel(logrus.InfoLevel)
	}
	
	// Set formatter based on environment
	if logFormat == "json" || isProduction {
		logger.SetFormatter(&CustomJSONFormatter{ServiceName: serviceName})
	} else {
		logger.SetFormatter(&CustomTextFormatter{
			ServiceName:   serviceName,
			IsDevelopment: isDevelopment,
		})
	}
	
	standardLogger := &StandardLogger{
		logger:      logger,
		serviceName: serviceName,
	}
	
	// Log initialization
	standardLogger.Info("Logger initialized", nil, map[string]interface{}{
		"logLevel":     logLevel,
		"logFormat":    logFormat,
		"environment":  environment,
	})
	
	return standardLogger
}

// CustomJSONFormatter provides JSON formatting for production
type CustomJSONFormatter struct {
	ServiceName string
}

func (f *CustomJSONFormatter) Format(entry *logrus.Entry) ([]byte, error) {
	correlationID := ""
	if corrID, exists := entry.Data["correlationId"]; exists {
		if id, ok := corrID.(string); ok {
			correlationID = id
		}
	}
	
	logEntry := LogEntry{
		Timestamp:     entry.Time,
		Level:         strings.ToUpper(entry.Level.String()),
		Service:       f.ServiceName,
		CorrelationID: correlationID,
		Message:       entry.Message,
		Metadata:      make(map[string]interface{}),
	}
	
	// Extract special fields
	if userID, exists := entry.Data["userId"]; exists {
		if id, ok := userID.(string); ok {
			logEntry.UserID = id
		}
	}
	
	if operation, exists := entry.Data["operation"]; exists {
		if op, ok := operation.(string); ok {
			logEntry.Operation = op
		}
	}
	
	if duration, exists := entry.Data["duration"]; exists {
		if dur, ok := duration.(int64); ok {
			logEntry.Duration = dur
		}
	}
	
	// Add remaining fields to metadata
	for key, value := range entry.Data {
		if key != "correlationId" && key != "userId" && key != "operation" && key != "duration" {
			logEntry.Metadata[key] = value
		}
	}
	
	// Remove metadata if empty
	if len(logEntry.Metadata) == 0 {
		logEntry.Metadata = nil
	}
	
	data, err := json.Marshal(logEntry)
	if err != nil {
		return nil, err
	}
	
	return append(data, '\n'), nil
}

// CustomTextFormatter provides colored text formatting for development
type CustomTextFormatter struct {
	ServiceName   string
	IsDevelopment bool
}

func (f *CustomTextFormatter) Format(entry *logrus.Entry) ([]byte, error) {
	timestamp := entry.Time.Format(time.RFC3339)
	
	correlationID := "no-correlation"
	if corrID, exists := entry.Data["correlationId"]; exists {
		if id, ok := corrID.(string); ok {
			correlationID = id
		}
	}
	
	// Build metadata string
	metaFields := []string{}
	
	if userID, exists := entry.Data["userId"]; exists {
		if id, ok := userID.(string); ok {
			metaFields = append(metaFields, fmt.Sprintf("userId=%s", id))
		}
	}
	
	if operation, exists := entry.Data["operation"]; exists {
		if op, ok := operation.(string); ok {
			metaFields = append(metaFields, fmt.Sprintf("operation=%s", op))
		}
	}
	
	if duration, exists := entry.Data["duration"]; exists {
		if dur, ok := duration.(int64); ok {
			metaFields = append(metaFields, fmt.Sprintf("duration=%dms", dur))
		}
	}
	
	// Add other metadata
	for key, value := range entry.Data {
		if key != "correlationId" && key != "userId" && key != "operation" && key != "duration" {
			metaFields = append(metaFields, fmt.Sprintf("%s=%v", key, value))
		}
	}
	
	metaStr := ""
	if len(metaFields) > 0 {
		metaStr = fmt.Sprintf(" | %s", strings.Join(metaFields, ", "))
	}
	
	level := strings.ToUpper(entry.Level.String())
	message := fmt.Sprintf("[%s] [%s] %s [%s]: %s%s\n", 
		timestamp, level, f.ServiceName, correlationID, entry.Message, metaStr)
	
	// Add colors for development
	if f.IsDevelopment {
		return []byte(f.colorize(level, message)), nil
	}
	
	return []byte(message), nil
}

func (f *CustomTextFormatter) colorize(level, message string) string {
	switch level {
	case "DEBUG":
		return fmt.Sprintf("\033[94m%s\033[0m", message) // Blue
	case "INFO":
		return fmt.Sprintf("\033[92m%s\033[0m", message) // Green
	case "WARN":
		return fmt.Sprintf("\033[93m%s\033[0m", message) // Yellow
	case "ERROR":
		return fmt.Sprintf("\033[91m%s\033[0m", message) // Red
	case "FATAL":
		return fmt.Sprintf("\033[95m%s\033[0m", message) // Magenta
	default:
		return message
	}
}

// Helper function to get environment variable with default
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// Logging methods

func (l *StandardLogger) log(level logrus.Level, message string, c *gin.Context, metadata map[string]interface{}) {
	fields := logrus.Fields{}
	
	// Add correlation ID
	if c != nil {
		correlationID := middleware.GetCorrelationID(c)
		fields["correlationId"] = correlationID
	}
	
	// Add metadata
	if metadata != nil {
		for key, value := range metadata {
			if value != nil {
				fields[key] = value
			}
		}
	}
	
	l.logger.WithFields(fields).Log(level, message)
}

func (l *StandardLogger) Info(message string, c *gin.Context, metadata map[string]interface{}) {
	l.log(logrus.InfoLevel, message, c, metadata)
}

func (l *StandardLogger) Debug(message string, c *gin.Context, metadata map[string]interface{}) {
	l.log(logrus.DebugLevel, message, c, metadata)
}

func (l *StandardLogger) Warn(message string, c *gin.Context, metadata map[string]interface{}) {
	l.log(logrus.WarnLevel, message, c, metadata)
}

func (l *StandardLogger) Error(message string, c *gin.Context, metadata map[string]interface{}) {
	l.log(logrus.ErrorLevel, message, c, metadata)
}

func (l *StandardLogger) Fatal(message string, c *gin.Context, metadata map[string]interface{}) {
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["level"] = "FATAL"
	l.log(logrus.FatalLevel, message, c, metadata)
}

func (l *StandardLogger) OperationStart(operation string, c *gin.Context, metadata map[string]interface{}) int64 {
	startTime := time.Now().UnixMilli()
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["operation"] = operation
	metadata["operationStart"] = true
	l.Debug(fmt.Sprintf("Starting operation: %s", operation), c, metadata)
	return startTime
}

func (l *StandardLogger) OperationComplete(operation string, startTime int64, c *gin.Context, metadata map[string]interface{}) int64 {
	duration := time.Now().UnixMilli() - startTime
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["operation"] = operation
	metadata["duration"] = duration
	metadata["operationComplete"] = true
	l.Info(fmt.Sprintf("Completed operation: %s", operation), c, metadata)
	return duration
}

func (l *StandardLogger) OperationFailed(operation string, startTime int64, err error, c *gin.Context, metadata map[string]interface{}) int64 {
	duration := time.Now().UnixMilli() - startTime
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["operation"] = operation
	metadata["duration"] = duration
	metadata["error"] = map[string]interface{}{
		"type":    fmt.Sprintf("%T", err),
		"message": err.Error(),
	}
	metadata["operationFailed"] = true
	l.Error(fmt.Sprintf("Failed operation: %s", operation), c, metadata)
	return duration
}

func (l *StandardLogger) Business(event string, c *gin.Context, metadata map[string]interface{}) {
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["businessEvent"] = event
	l.Info(fmt.Sprintf("Business event: %s", event), c, metadata)
}

func (l *StandardLogger) Security(event string, c *gin.Context, metadata map[string]interface{}) {
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["securityEvent"] = event
	l.Warn(fmt.Sprintf("Security event: %s", event), c, metadata)
}

func (l *StandardLogger) Performance(operation string, duration int64, c *gin.Context, metadata map[string]interface{}) {
	if metadata == nil {
		metadata = make(map[string]interface{})
	}
	metadata["operation"] = operation
	metadata["duration"] = duration
	metadata["performance"] = true
	
	message := fmt.Sprintf("Performance: %s", operation)
	if duration > 1000 {
		l.Warn(message, c, metadata)
	} else {
		l.Info(message, c, metadata)
	}
}
