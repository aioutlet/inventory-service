-- Inventory Service Database Initialization
-- This script sets up the initial database schema and indexes

-- Use the inventory database
USE inventory_db;

-- Enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Create inventory_items table with proper indexes
CREATE TABLE IF NOT EXISTS inventory_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(255) NOT NULL UNIQUE,
    quantity INT NOT NULL DEFAULT 0,
    reserved_quantity INT NOT NULL DEFAULT 0,
    minimum_stock_level INT NOT NULL DEFAULT 0,
    maximum_stock_level INT DEFAULT NULL,
    location VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Add indexes for better performance
    INDEX idx_product_id (product_id),
    INDEX idx_location (location),
    INDEX idx_quantity (quantity),
    INDEX idx_reserved_quantity (reserved_quantity),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    
    -- Add constraints
    CONSTRAINT chk_quantity_non_negative CHECK (quantity >= 0),
    CONSTRAINT chk_reserved_quantity_non_negative CHECK (reserved_quantity >= 0),
    CONSTRAINT chk_reserved_not_greater_than_total CHECK (reserved_quantity <= quantity),
    CONSTRAINT chk_minimum_stock_non_negative CHECK (minimum_stock_level >= 0),
    CONSTRAINT chk_maximum_stock_positive CHECK (maximum_stock_level IS NULL OR maximum_stock_level > 0),
    CONSTRAINT chk_max_greater_than_min CHECK (maximum_stock_level IS NULL OR maximum_stock_level >= minimum_stock_level)
);

-- Create reservations table
CREATE TABLE IF NOT EXISTS reservations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_item_id INT NOT NULL,
    quantity INT NOT NULL,
    customer_id VARCHAR(255) NOT NULL,
    order_id VARCHAR(255) NOT NULL,
    status ENUM('ACTIVE', 'CONFIRMED', 'CANCELLED', 'EXPIRED') NOT NULL DEFAULT 'ACTIVE',
    expires_at TIMESTAMP NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    -- Add indexes for better performance
    INDEX idx_inventory_item_id (inventory_item_id),
    INDEX idx_customer_id (customer_id),
    INDEX idx_order_id (order_id),
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    
    -- Composite indexes for common queries
    INDEX idx_customer_order (customer_id, order_id),
    INDEX idx_status_expires (status, expires_at),
    
    -- Add constraints
    CONSTRAINT chk_reservation_quantity_positive CHECK (quantity > 0)
);

-- Create stock_movements table
CREATE TABLE IF NOT EXISTS stock_movements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    inventory_item_id INT NOT NULL,
    movement_type ENUM('INBOUND', 'OUTBOUND', 'ADJUSTMENT', 'TRANSFER', 'RETURN', 'DAMAGE', 'LOSS') NOT NULL,
    quantity INT NOT NULL,
    reference_id VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (inventory_item_id) REFERENCES inventory_items(id) ON DELETE CASCADE ON UPDATE CASCADE,
    
    -- Add indexes for better performance
    INDEX idx_inventory_item_id (inventory_item_id),
    INDEX idx_movement_type (movement_type),
    INDEX idx_reference_id (reference_id),
    INDEX idx_created_at (created_at),
    
    -- Composite indexes for common queries
    INDEX idx_item_type (inventory_item_id, movement_type),
    INDEX idx_item_created (inventory_item_id, created_at),
    
    -- Add constraints
    CONSTRAINT chk_movement_quantity_not_zero CHECK (quantity != 0)
);

-- Insert some sample data for testing (only if tables are empty)
INSERT IGNORE INTO inventory_items (product_id, quantity, reserved_quantity, minimum_stock_level, maximum_stock_level, location)
VALUES 
    ('SAMPLE001', 100, 0, 10, 500, 'Warehouse A'),
    ('SAMPLE002', 250, 25, 20, 1000, 'Warehouse B'),
    ('SAMPLE003', 75, 5, 15, 300, 'Warehouse A'),
    ('SAMPLE004', 500, 50, 50, 2000, 'Warehouse C'),
    ('SAMPLE005', 10, 0, 25, 200, 'Warehouse B');

-- Create a view for inventory with computed columns
CREATE OR REPLACE VIEW inventory_overview AS
SELECT 
    ii.id,
    ii.product_id,
    ii.quantity,
    ii.reserved_quantity,
    (ii.quantity - ii.reserved_quantity) AS available_quantity,
    ii.minimum_stock_level,
    ii.maximum_stock_level,
    ii.location,
    (ii.quantity - ii.reserved_quantity) <= ii.minimum_stock_level AS is_low_stock,
    (ii.quantity - ii.reserved_quantity) <= 0 AS is_out_of_stock,
    ii.created_at,
    ii.updated_at
FROM inventory_items ii;

-- Create a view for active reservations summary
CREATE OR REPLACE VIEW active_reservations_summary AS
SELECT 
    ii.product_id,
    ii.location,
    COUNT(r.id) AS active_reservation_count,
    SUM(r.quantity) AS total_reserved_quantity,
    MIN(r.expires_at) AS earliest_expiration
FROM inventory_items ii
LEFT JOIN reservations r ON ii.id = r.inventory_item_id AND r.status = 'ACTIVE'
GROUP BY ii.id, ii.product_id, ii.location;

-- Create indexes on views (MySQL 8.0+ supports functional indexes)
-- CREATE INDEX idx_low_stock ON inventory_overview ((quantity - reserved_quantity <= minimum_stock_level));
-- CREATE INDEX idx_out_of_stock ON inventory_overview ((quantity - reserved_quantity <= 0));

-- Grant permissions to the application user
GRANT SELECT, INSERT, UPDATE, DELETE ON inventory_db.* TO 'inventory_user'@'%';
GRANT CREATE, DROP, ALTER ON inventory_db.* TO 'inventory_user'@'%';
FLUSH PRIVILEGES;

-- Display summary of created objects
SELECT 'Database initialization completed successfully' AS status;
SELECT COUNT(*) AS inventory_items_count FROM inventory_items;
SELECT COUNT(*) AS reservations_count FROM reservations;
SELECT COUNT(*) AS stock_movements_count FROM stock_movements;
