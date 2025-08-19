-- Inventory Service Schema
-- Handles product inventory, stock levels, and warehouse management

CREATE SCHEMA IF NOT EXISTS inventory;

-- Warehouses/Locations
CREATE TABLE IF NOT EXISTS inventory.warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    address JSONB NOT NULL,
    contact_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product inventory levels
CREATE TABLE IF NOT EXISTS inventory.stock_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL, -- Reference to product service
    warehouse_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    quantity_incoming INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER DEFAULT 10,
    max_stock_level INTEGER DEFAULT 1000,
    cost_per_unit DECIMAL(10, 2),
    last_restock_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES inventory.warehouses(id) ON DELETE CASCADE,
    UNIQUE(product_id, warehouse_id, sku)
);

-- Stock movements/transactions
CREATE TABLE IF NOT EXISTS inventory.stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL,
    warehouse_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    movement_type VARCHAR(50) NOT NULL, -- 'in', 'out', 'adjustment', 'transfer', 'damaged', 'returned'
    quantity INTEGER NOT NULL,
    unit_cost DECIMAL(10, 2),
    reference_type VARCHAR(50), -- 'purchase', 'sale', 'adjustment', 'transfer'
    reference_id VARCHAR(255), -- Reference to order, purchase, etc.
    notes TEXT,
    performed_by UUID, -- User who performed the movement
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES inventory.warehouses(id) ON DELETE CASCADE
);

-- Low stock alerts
CREATE TABLE IF NOT EXISTS inventory.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL,
    warehouse_id UUID NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'low_stock', 'out_of_stock', 'overstock'
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES inventory.warehouses(id) ON DELETE CASCADE
);

-- Inventory reservations (for orders)
CREATE TABLE IF NOT EXISTS inventory.reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(24) NOT NULL,
    warehouse_id UUID NOT NULL,
    sku VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    order_id VARCHAR(255) NOT NULL, -- Reference to order service
    customer_id UUID NOT NULL, -- Reference to user service
    expires_at TIMESTAMP NOT NULL,
    is_fulfilled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (warehouse_id) REFERENCES inventory.warehouses(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_warehouses_code ON inventory.warehouses(code);
CREATE INDEX IF NOT EXISTS idx_warehouses_active ON inventory.warehouses(is_active);
CREATE INDEX IF NOT EXISTS idx_stock_levels_product_id ON inventory.stock_levels(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_levels_warehouse_id ON inventory.stock_levels(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_levels_sku ON inventory.stock_levels(sku);
CREATE INDEX IF NOT EXISTS idx_stock_levels_quantity ON inventory.stock_levels(quantity_available);
CREATE INDEX IF NOT EXISTS idx_stock_movements_product_id ON inventory.stock_movements(product_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse_id ON inventory.stock_movements(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON inventory.stock_movements(movement_type);
CREATE INDEX IF NOT EXISTS idx_stock_movements_created_at ON inventory.stock_movements(created_at);
CREATE INDEX IF NOT EXISTS idx_alerts_product_id ON inventory.alerts(product_id);
CREATE INDEX IF NOT EXISTS idx_alerts_warehouse_id ON inventory.alerts(warehouse_id);
CREATE INDEX IF NOT EXISTS idx_alerts_resolved ON inventory.alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_reservations_product_id ON inventory.reservations(product_id);
CREATE INDEX IF NOT EXISTS idx_reservations_order_id ON inventory.reservations(order_id);
CREATE INDEX IF NOT EXISTS idx_reservations_expires_at ON inventory.reservations(expires_at);
