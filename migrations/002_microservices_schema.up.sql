-- Updated Inventory Service Schema - Microservices Best Practices
-- This schema removes the products table and uses external product references

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Inventory items table (main table - no product duplication)
CREATE TABLE inventory_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id VARCHAR(24) NOT NULL, -- MongoDB ObjectId from product service (24 hex chars)
    sku VARCHAR(100) UNIQUE NOT NULL, -- Business identifier for queries
    quantity_available INTEGER NOT NULL DEFAULT 0,
    quantity_reserved INTEGER NOT NULL DEFAULT 0,
    reorder_level INTEGER NOT NULL DEFAULT 0,
    max_stock INTEGER NOT NULL DEFAULT 1000,
    warehouse_location VARCHAR(50),
    supplier VARCHAR(255),
    cost_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    last_restocked TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'in_stock',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT positive_quantities CHECK (
        quantity_available >= 0 AND 
        quantity_reserved >= 0 AND 
        reorder_level >= 0 AND 
        max_stock >= 0
    ),
    CONSTRAINT valid_status CHECK (status IN ('in_stock', 'low_stock', 'out_of_stock', 'discontinued')),
    CONSTRAINT valid_mongodb_id CHECK (product_id ~ '^[0-9a-fA-F]{24}$') -- Validate MongoDB ObjectId format
);

-- Reservations table
CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL,
    product_id VARCHAR(24) NOT NULL, -- MongoDB ObjectId
    sku VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'confirmed', 'released', 'expired')),
    CONSTRAINT valid_mongodb_id CHECK (product_id ~ '^[0-9a-fA-F]{24}$')
);

-- Stock movements table for audit trail
CREATE TABLE stock_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id VARCHAR(24) NOT NULL, -- MongoDB ObjectId
    sku VARCHAR(100) NOT NULL,
    movement_type VARCHAR(20) NOT NULL,
    quantity INTEGER NOT NULL,
    reference VARCHAR(255), -- Order ID, Restock ID, etc.
    reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255) NOT NULL DEFAULT 'system',
    
    CONSTRAINT valid_movement_type CHECK (
        movement_type IN ('in', 'out', 'reserved', 'released', 'adjustment')
    ),
    CONSTRAINT valid_mongodb_id CHECK (product_id ~ '^[0-9a-fA-F]{24}$')
);

-- Indexes for performance
CREATE INDEX idx_inventory_sku ON inventory_items(sku);
CREATE INDEX idx_inventory_product_id ON inventory_items(product_id);
CREATE INDEX idx_inventory_status ON inventory_items(status);
CREATE INDEX idx_inventory_reorder ON inventory_items(reorder_level) WHERE quantity_available <= reorder_level;
CREATE INDEX idx_inventory_warehouse ON inventory_items(warehouse_location);

CREATE INDEX idx_reservations_order_id ON reservations(order_id);
CREATE INDEX idx_reservations_product_id ON reservations(product_id);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_reservations_expires_at ON reservations(expires_at);
CREATE INDEX idx_reservations_sku ON reservations(sku);

CREATE INDEX idx_stock_movements_product_id ON stock_movements(product_id);
CREATE INDEX idx_stock_movements_sku ON stock_movements(sku);
CREATE INDEX idx_stock_movements_type ON stock_movements(movement_type);
CREATE INDEX idx_stock_movements_created_at ON stock_movements(created_at);
CREATE INDEX idx_stock_movements_reference ON stock_movements(reference);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_inventory_items_updated_at 
    BEFORE UPDATE ON inventory_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_reservations_updated_at 
    BEFORE UPDATE ON reservations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically update inventory status based on quantity
CREATE OR REPLACE FUNCTION update_inventory_status()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.quantity_available = 0 THEN
        NEW.status = 'out_of_stock';
    ELSIF NEW.quantity_available <= NEW.reorder_level THEN
        NEW.status = 'low_stock';
    ELSE
        NEW.status = 'in_stock';
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_inventory_status_trigger
    BEFORE INSERT OR UPDATE OF quantity_available, reorder_level
    ON inventory_items
    FOR EACH ROW EXECUTE FUNCTION update_inventory_status();
