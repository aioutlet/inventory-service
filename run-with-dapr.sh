#!/bin/bash

# =============================================================================
# Inventory Service - Run with Dapr Sidecar
# =============================================================================
# This script starts the inventory service with Dapr sidecar for event-driven
# communication using RabbitMQ pub/sub.

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Inventory Service with Dapr${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Dapr CLI is installed
if ! command -v dapr &> /dev/null; then
    echo -e "${YELLOW}⚠️  Dapr CLI not found!${NC}"
    echo "Please install Dapr CLI: https://docs.dapr.io/getting-started/install-dapr-cli/"
    exit 1
fi

# Check if Dapr is initialized
if ! dapr --version &> /dev/null; then
    echo -e "${YELLOW}⚠️  Dapr not initialized!${NC}"
    echo "Run: dapr init"
    exit 1
fi

# Configuration
APP_ID="inventory-service"
APP_PORT=5000
DAPR_HTTP_PORT=3502
DAPR_GRPC_PORT=50002
COMPONENTS_PATH="./.dapr/components"
CONFIG_PATH="./.dapr/config.yaml"

echo -e "${GREEN}📋 Configuration:${NC}"
echo "  App ID: $APP_ID"
echo "  App Port: $APP_PORT"
echo "  Dapr HTTP Port: $DAPR_HTTP_PORT"
echo "  Dapr gRPC Port: $DAPR_GRPC_PORT"
echo "  Components Path: $COMPONENTS_PATH"
echo "  Config Path: $CONFIG_PATH"
echo ""

# Check if components directory exists
if [ ! -d "$COMPONENTS_PATH" ]; then
    echo -e "${YELLOW}⚠️  Components directory not found: $COMPONENTS_PATH${NC}"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo -e "${YELLOW}⚠️  Config file not found: $CONFIG_PATH${NC}"
    exit 1
fi

echo -e "${GREEN}🚀 Starting Inventory Service with Dapr sidecar...${NC}"
echo ""

# Run with Dapr
dapr run \
  --app-id "$APP_ID" \
  --app-port "$APP_PORT" \
  --dapr-http-port "$DAPR_HTTP_PORT" \
  --dapr-grpc-port "$DAPR_GRPC_PORT" \
  --components-path "$COMPONENTS_PATH" \
  --config "$CONFIG_PATH" \
  --log-level info \
  -- python run.py

# Note: The above command will:
# 1. Start Dapr sidecar on ports 3502 (HTTP) and 50002 (gRPC)
# 2. Start Flask app on port 5002
# 3. Connect to RabbitMQ for pub/sub via components/pubsub.yaml
# 4. Enable tracing to Zipkin (if configured)
# 5. Provide service invocation via Dapr
