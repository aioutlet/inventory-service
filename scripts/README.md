# Inventory Service Data Seeding

This directory contains tools and data for seeding the inventory service database with sample data.

## 📁 Files

- **`inventory-data.json`** - Enhanced inventory data with realistic product information
- **`seed.sh`** - Bash script for convenient seeding operations (Linux/macOS)
- **`seed.ps1`** - PowerShell script for convenient seeding operations (Windows)

## 🚀 Quick Start

### Using the Convenience Scripts

**Linux/macOS (Bash):**

```bash
# Make script executable
chmod +x scripts/seed.sh

# Seed with default data
./scripts/seed.sh seed

# Clear and reseed with verbose output
./scripts/seed.sh clear-and-seed --verbose

# Seed with custom data file
./scripts/seed.sh seed-file scripts/inventory-data.json
```

**Windows (PowerShell):**

```powershell
# Seed with default data
.\scripts\seed.ps1 seed

# Clear and reseed with verbose output
.\scripts\seed.ps1 clear-and-seed -Verbose

# Seed with custom data file
.\scripts\seed.ps1 seed-file scripts\inventory-data.json
```

### Using the Go Binary Directly

```bash
# Build the seeder
go build -o bin/seed ./cmd/seed

# Run with default sample data
./bin/seed

# Clear existing data and reseed
./bin/seed -clear

# Load from JSON file
./bin/seed -file scripts/inventory-data.json

# Verbose output with summary
./bin/seed -verbose -summary

# Clear and load from file
./bin/seed -clear -file scripts/inventory-data.json
```

## 📊 Data Format

### Enhanced Inventory Data Format (`inventory-data.json`)

```json
[
  {
    "product_id": "1",
    "product_sku": "APL-IPH15-PRO-128",
    "product_name": "iPhone 15 Pro",
    "quantity": 45,
    "reserved_quantity": 3,
    "min_stock_level": 10,
    "max_stock_level": 100,
    "warehouse_location": "A-01-15",
    "supplier": "Apple Inc",
    "cost_price": 799.99,
    "last_restocked": "2024-01-15T10:30:00Z",
    "status": "in_stock"
  }
]
```

### Simple Product Format (Fallback)

```json
[
  {
    "sku": "LAPTOP-001",
    "name": "MacBook Pro 16-inch",
    "description": "Apple MacBook Pro with M2 chip",
    "price": 2499.99,
    "category": "Laptops",
    "stock": 25,
    "reorder_level": 5,
    "max_stock": 100
  }
]
```

## 🎯 Available Commands

### Convenience Script Commands

| Command                      | Description                             |
| ---------------------------- | --------------------------------------- |
| `build`                      | Build the seeder binary                 |
| `seed`                       | Run seeder with default data            |
| `seed-file <file>`           | Run seeder with custom JSON file        |
| `clear`                      | Clear all existing data                 |
| `clear-and-seed`             | Clear data and reseed with default data |
| `clear-and-seed-file <file>` | Clear data and reseed with custom file  |
| `summary`                    | Show database summary without seeding   |

### Options

| Option                        | Description                   |
| ----------------------------- | ----------------------------- |
| `--verbose` / `-Verbose`      | Enable detailed logging       |
| `--no-summary` / `-NoSummary` | Disable summary after seeding |

### Direct Binary Flags

| Flag           | Description                           |
| -------------- | ------------------------------------- |
| `-clear`       | Clear existing data before seeding    |
| `-file <path>` | Load data from JSON file              |
| `-verbose`     | Enable verbose logging                |
| `-summary`     | Show database summary (default: true) |

## 📋 Sample Data

The `inventory-data.json` file includes:

- **12 inventory items** with realistic product data
- **Stock levels** ranging from out-of-stock to well-stocked
- **Reserved quantities** for some items
- **Warehouse locations** in a realistic format
- **Cost prices** with supplier information
- **Different stock statuses**: `in_stock`, `low_stock`, `out_of_stock`
- **Test items** for edge case testing

### Product Categories Included

- Electronics (iPhones, Samsung Galaxy, etc.)
- Computers (MacBook, Dell XPS, etc.)
- Tablets (iPad Pro, etc.)
- Audio (Sony headphones, AirPods, etc.)
- Home appliances (Dyson, LG TV, etc.)
- Gaming (Nintendo Switch, etc.)

## 🔧 Integration with Other Services

The inventory data is designed to align with the product service data:

- **SKUs match** between inventory and product services
- **Product names** are consistent
- **Stock quantities** reflect realistic inventory levels
- **Test items** included for edge case testing

## ⚡ Performance Notes

- Uses **database transactions** for data consistency
- Supports **bulk inserts** for large datasets
- Includes **conflict resolution** (ON CONFLICT DO UPDATE)
- **Connection pooling** handled by the database layer

## 🧪 Testing Integration

After seeding, you can:

1. **Verify data** using the summary command
2. **Test API endpoints** with known SKUs
3. **Check stock levels** and reservations
4. **Test low stock alerts** with test items
5. **Validate warehouse operations** with location data

## 🔍 Troubleshooting

### Common Issues

1. **Database connection errors**: Check your `.env` file and database URL
2. **Permission errors**: Ensure database user has INSERT/UPDATE/DELETE permissions
3. **Build failures**: Verify Go installation and dependencies
4. **File not found**: Check file paths and working directory

### Debug Commands

```bash
# Test database connection
./bin/seed -summary

# Verbose logging for detailed error info
./bin/seed -verbose

# Check if data exists
./bin/seed -summary | grep "Products:"
```

## 📝 Logs

The seeder provides detailed logging:

- ✅ **Success indicators** for completed operations
- ⚠️ **Warnings** for non-critical issues
- ❌ **Errors** for failures
- 📊 **Summary statistics** after completion
- 🔍 **Verbose details** when enabled

## 🔄 Integration with Build System

The seeding scripts integrate with the main build system:

```bash
# Run as part of development setup
./scripts/build-service.sh inventory-service
./scripts/seed.sh seed

# Include in testing workflow
./scripts/seed.sh clear-and-seed
npm test  # or your test command
```
