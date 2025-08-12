package client

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"inventory-service/internal/middleware"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
)

// ServiceClient provides HTTP client functionality with correlation ID support
type ServiceClient struct {
	BaseURL    string
	HTTPClient *http.Client
	Logger     *logrus.Logger
}

// NewServiceClient creates a new service client
func NewServiceClient(baseURL string, timeout time.Duration, logger *logrus.Logger) *ServiceClient {
	return &ServiceClient{
		BaseURL: baseURL,
		HTTPClient: &http.Client{
			Timeout: timeout,
		},
		Logger: logger,
	}
}

// createRequest creates an HTTP request with correlation ID headers
func (c *ServiceClient) createRequest(ctx context.Context, method, endpoint string, body interface{}) (*http.Request, error) {
	var reqBody io.Reader
	
	if body != nil {
		jsonData, err := json.Marshal(body)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal request body: %w", err)
		}
		reqBody = bytes.NewBuffer(jsonData)
	}
	
	url := c.BaseURL + endpoint
	req, err := http.NewRequestWithContext(ctx, method, url, reqBody)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}
	
	// Set correlation ID header
	correlationID := middleware.GetCorrelationIDFromContext(ctx)
	req.Header.Set("X-Correlation-ID", correlationID)
	req.Header.Set("Content-Type", "application/json")
	
	return req, nil
}

// Get makes a GET request with correlation ID
func (c *ServiceClient) Get(ctx context.Context, endpoint string) (*http.Response, error) {
	req, err := c.createRequest(ctx, http.MethodGet, endpoint, nil)
	if err != nil {
		return nil, err
	}
	
	correlationID := middleware.GetCorrelationIDFromContext(ctx)
	c.Logger.WithField("correlationId", correlationID).
		Debugf("Making GET request to %s", req.URL.String())
	
	return c.HTTPClient.Do(req)
}

// Post makes a POST request with correlation ID
func (c *ServiceClient) Post(ctx context.Context, endpoint string, body interface{}) (*http.Response, error) {
	req, err := c.createRequest(ctx, http.MethodPost, endpoint, body)
	if err != nil {
		return nil, err
	}
	
	correlationID := middleware.GetCorrelationIDFromContext(ctx)
	c.Logger.WithField("correlationId", correlationID).
		Debugf("Making POST request to %s", req.URL.String())
	
	return c.HTTPClient.Do(req)
}

// Put makes a PUT request with correlation ID
func (c *ServiceClient) Put(ctx context.Context, endpoint string, body interface{}) (*http.Response, error) {
	req, err := c.createRequest(ctx, http.MethodPut, endpoint, body)
	if err != nil {
		return nil, err
	}
	
	correlationID := middleware.GetCorrelationIDFromContext(ctx)
	c.Logger.WithField("correlationId", correlationID).
		Debugf("Making PUT request to %s", req.URL.String())
	
	return c.HTTPClient.Do(req)
}

// Delete makes a DELETE request with correlation ID
func (c *ServiceClient) Delete(ctx context.Context, endpoint string) (*http.Response, error) {
	req, err := c.createRequest(ctx, http.MethodDelete, endpoint, nil)
	if err != nil {
		return nil, err
	}
	
	correlationID := middleware.GetCorrelationIDFromContext(ctx)
	c.Logger.WithField("correlationId", correlationID).
		Debugf("Making DELETE request to %s", req.URL.String())
	
	return c.HTTPClient.Do(req)
}

// GetWithGinContext makes a GET request using Gin context for correlation ID
func (c *ServiceClient) GetWithGinContext(ginCtx *gin.Context, endpoint string) (*http.Response, error) {
	return c.Get(ginCtx.Request.Context(), endpoint)
}

// PostWithGinContext makes a POST request using Gin context for correlation ID
func (c *ServiceClient) PostWithGinContext(ginCtx *gin.Context, endpoint string, body interface{}) (*http.Response, error) {
	return c.Post(ginCtx.Request.Context(), endpoint, body)
}

// PutWithGinContext makes a PUT request using Gin context for correlation ID
func (c *ServiceClient) PutWithGinContext(ginCtx *gin.Context, endpoint string, body interface{}) (*http.Response, error) {
	return c.Put(ginCtx.Request.Context(), endpoint, body)
}

// DeleteWithGinContext makes a DELETE request using Gin context for correlation ID
func (c *ServiceClient) DeleteWithGinContext(ginCtx *gin.Context, endpoint string) (*http.Response, error) {
	return c.Delete(ginCtx.Request.Context(), endpoint)
}
