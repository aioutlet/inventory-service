-- Rollback migration for microservices schema
-- This reverts back to the original schema with products table

DROP TRIGGER IF EXISTS update_inventory_status_trigger ON inventory_items;
DROP FUNCTION IF EXISTS update_inventory_status();
DROP TRIGGER IF EXISTS update_inventory_items_updated_at ON inventory_items;
DROP TRIGGER IF EXISTS update_reservations_updated_at ON reservations;
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_inventory_warehouse;
DROP INDEX IF EXISTS idx_inventory_status;
DROP INDEX IF EXISTS idx_inventory_sku;
DROP INDEX IF EXISTS idx_inventory_product_id;
DROP INDEX IF EXISTS idx_inventory_reorder;
DROP INDEX IF EXISTS idx_reservations_order_id;
DROP INDEX IF EXISTS idx_reservations_product_id;
DROP INDEX IF EXISTS idx_reservations_status;
DROP INDEX IF EXISTS idx_reservations_expires_at;
DROP INDEX IF EXISTS idx_reservations_sku;
DROP INDEX IF EXISTS idx_stock_movements_product_id;
DROP INDEX IF EXISTS idx_stock_movements_sku;
DROP INDEX IF EXISTS idx_stock_movements_type;
DROP INDEX IF EXISTS idx_stock_movements_created_at;
DROP INDEX IF EXISTS idx_stock_movements_reference;

-- Drop tables
DROP TABLE IF EXISTS stock_movements;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS inventory_items;

-- Drop extension if no other tables use it
DROP EXTENSION IF EXISTS "uuid-ossp";
