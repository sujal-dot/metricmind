
# MetricMind Cube.dev Semantic Layer

This directory contains the Cube.dev semantic layer configuration for MetricMind's business intelligence platform.

## Project Structure
```
cube/
├── model/                  # Semantic models
│   ├── dim_customer.js     # Customer dimension
│   ├── dim_date.js         # Date dimension
│   ├── dim_employee.js     # Employee dimension
│   ├── dim_product.js      # Product dimension
│   ├── dim_region.js       # Region dimension
│   └── fact_sales.js       # Sales fact with all measures & joins
├── .env                    # Environment variables
├── cube.js                 # Cube configuration
├── package.json            # NPM dependencies
└── validate.js             # Validation script
```

## Getting Started
1. Install dependencies:
   ```bash
   cd cube
   npm install
   ```
2. Run validation script (checks everything):
   ```bash
   node validate.js
   ```
3. Start Cube server:
   ```bash
   npm run dev
   ```
4. Open http://localhost:4000 in your browser to explore the Playground!

## Day7: Testing & Validation
To run the complete, automated Day7 validation:
1. Ensure PostgreSQL container is running:
   ```bash
   cd /path/to/metricmind
   docker-compose up -d
   ```
2. Install dependencies (if not already installed):
   ```bash
   cd cube
   npm install
   ```
3. Run automated validation test script:
   ```bash
   node test.js
   ```
This will:
- Start the Cube server
- Test PostgreSQL connection
- Verify all semantic models
- Test all measures, dimensions, time dimensions
- Execute sample analytical queries
- Validate JSON responses
- Generate logs and final report in ../backend/logs/
4. View the final report at ../backend/logs/day7-final-report.txt

## Environment Variables
Make sure your PostgreSQL credentials in `.env` match your docker-compose setup!
