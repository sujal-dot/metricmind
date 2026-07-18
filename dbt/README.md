
# MetricMind dbt Project

This is the dbt project for the MetricMind Agentic Business Intelligence platform.

## Project Structure
```
dbt/
├── models/
│   ├── staging/          # Staging models (cleaning source tables)
│   ├── intermediate/     # Intermediate models (joins, transformations)
│   ├── marts/            # Analytics-ready mart models
│   ├── sources.yml       # Source definitions
│   └── schema.yml        # Tests and documentation
├── macros/
├── seeds/
├── snapshots/
├── tests/
├── dbt_project.yml       # dbt project configuration
└── profiles.yml          # Database connection profiles
```

## Getting Started

### Prerequisites
- dbt installed (dbt-core and dbt-postgres)
- PostgreSQL database running (via docker-compose)

### Run dbt
```bash
cd dbt/
dbt debug --profiles-dir .          # Test connection
dbt run --profiles-dir .            # Run models
dbt test --profiles-dir .           # Run tests
dbt docs generate --profiles-dir .  # Generate docs
dbt docs serve --profiles-dir .     # Serve docs locally
```
