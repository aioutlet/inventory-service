package middleware

import (
	"context"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
)

const (
	CorrelationIDHeader = "X-Correlation-ID"
	CorrelationIDKey    = "correlationId"
)

// CorrelationIDMiddleware adds correlation ID to request context for distributed tracing
func CorrelationIDMiddleware() gin.HandlerFunc {
	return gin.HandlerFunc(func(c *gin.Context) {
		// Get correlation ID from header or generate new one
		correlationID := c.GetHeader(CorrelationIDHeader)
		if correlationID == "" {
			correlationID = uuid.New().String()
		}

		// Set correlation ID in context
		ctx := context.WithValue(c.Request.Context(), CorrelationIDKey, correlationID)
		c.Request = c.Request.WithContext(ctx)

		// Set correlation ID in Gin context for easy access
		c.Set(CorrelationIDKey, correlationID)

		// Add correlation ID to response headers
		c.Header(CorrelationIDHeader, correlationID)

		// Log request with correlation ID
		logrus.WithField("correlationId", correlationID).
			Infof("Processing request %s %s", c.Request.Method, c.Request.URL.Path)

		c.Next()
	})
}

// GetCorrelationID retrieves correlation ID from Gin context
func GetCorrelationID(c *gin.Context) string {
	if correlationID, exists := c.Get(CorrelationIDKey); exists {
		if id, ok := correlationID.(string); ok {
			return id
		}
	}
	return "unknown"
}

// GetCorrelationIDFromContext retrieves correlation ID from context
func GetCorrelationIDFromContext(ctx context.Context) string {
	if correlationID := ctx.Value(CorrelationIDKey); correlationID != nil {
		if id, ok := correlationID.(string); ok {
			return id
		}
	}
	return "unknown"
}

// LogWithCorrelationID logs a message with correlation ID
func LogWithCorrelationID(c *gin.Context, level string, message string, fields logrus.Fields) {
	correlationID := GetCorrelationID(c)
	
	if fields == nil {
		fields = logrus.Fields{}
	}
	fields["correlationId"] = correlationID

	logger := logrus.WithFields(fields)
	
	switch level {
	case "debug":
		logger.Debug(message)
	case "info":
		logger.Info(message)
	case "warn":
		logger.Warn(message)
	case "error":
		logger.Error(message)
	default:
		logger.Info(message)
	}
}
