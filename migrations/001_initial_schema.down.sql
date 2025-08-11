-- Drop triggers
DROP TRIGGER IF EXISTS update_reservations_updated_at ON reservations;
DROP TRIGGER IF EXISTS update_inventory_items_updated_at ON inventory_items;
DROP TRIGGER IF EXISTS update_products_updated_at ON products;

-- Drop function
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_stock_movements_reference;
DROP INDEX IF EXISTS idx_stock_movements_created_at;
DROP INDEX IF EXISTS idx_stock_movements_type;
DROP INDEX IF EXISTS idx_stock_movements_sku;
DROP INDEX IF EXISTS idx_stock_movements_product_id;

DROP INDEX IF EXISTS idx_reservations_sku;
DROP INDEX IF EXISTS idx_reservations_expires_at;
DROP INDEX IF EXISTS idx_reservations_status;
DROP INDEX IF EXISTS idx_reservations_product_id;
DROP INDEX IF EXISTS idx_reservations_order_id;

DROP INDEX IF EXISTS idx_inventory_reorder;
DROP INDEX IF EXISTS idx_inventory_product_id;
DROP INDEX IF EXISTS idx_inventory_sku;

DROP INDEX IF EXISTS idx_products_active;
DROP INDEX IF EXISTS idx_products_category;
DROP INDEX IF EXISTS idx_products_sku;

-- Drop tables
DROP TABLE IF EXISTS stock_movements;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS inventory_items;
DROP TABLE IF EXISTS products;

-- Drop extension
DROP EXTENSION IF EXISTS "uuid-ossp";
