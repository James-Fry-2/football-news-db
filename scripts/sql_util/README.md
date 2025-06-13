# SQL Utility Scripts

This folder contains SQL scripts and utilities for analyzing the football news database.

## Quick Start

### Running SQL Scripts

```bash
# From the project root directory
cd scripts/sql_util

# Make script executable (Linux/Mac only)
chmod +x run_sql.sh

# Run a specific SQL script
./run_sql.sh articles_today.sql

# Enter interactive PostgreSQL mode
./run_sql.sh
```

### On Windows

```powershell
# From the project root directory
cd scripts/sql_util

# Run a specific SQL script
bash run_sql.sh articles_today.sql

# Enter interactive mode
bash run_sql.sh
```

## Available SQL Scripts

### 1. `articles_today.sql`
Shows articles uploaded today with key information including:
- Article details (ID, title, source, author)
- Upload and publish dates
- Processing status and sentiment scores
- Summary statistics for today's articles

### 2. `load_volumes_by_day.sql`
Analyzes article load volumes separated by day with:
- **Daily statistics** for the last 30 days
- **Weekly summaries** for the last 8 weeks  
- **Monthly summaries** for the last 6 months
- Processing rates and source diversity metrics

### 3. `article_sources_analysis.sql`
Comprehensive source analysis including:
- Article counts and processing statistics by source
- Daily trends for top 5 sources (last 14 days)
- Source performance comparison with sentiment analysis
- Processing time metrics by source

### 4. `recent_articles_summary.sql`
Recent articles overview featuring:
- Latest 20 articles with detailed information
- Hourly upload patterns for the last 24 hours
- Processing status breakdown
- Articles needing attention (failed or stuck processing)

### 5. `database_health_check.sql`
System health monitoring with:
- Overall database statistics and size information
- Data quality metrics (missing fields, duplicates)
- Processing pipeline health indicators
- Daily upload trends and performance metrics

## Script Features

### Environment Configuration
The `run_sql.sh` script automatically:
- Loads environment variables from `.env` file
- Validates required PostgreSQL connection variables
- Checks database connectivity before executing queries

### Output Formatting
- **Tabulated output**: Results are displayed in readable table format
- **Timing information**: Shows query execution time
- **Auto-expanding**: Large result sets automatically adjust column width
- **Color coding**: Info, warning, and error messages are color-coded

### Usage Examples

```bash
# View today's articles
./run_sql.sh articles_today.sql

# Check load volumes
./run_sql.sh load_volumes_by_day.sql

# Analyze sources performance
./run_sql.sh article_sources_analysis.sql

# Get recent articles summary
./run_sql.sh recent_articles_summary.sql

# Run health check
./run_sql.sh database_health_check.sql

# Interactive mode for custom queries
./run_sql.sh
```

## Requirements

### Environment Variables (from .env file)
- `POSTGRES_USER`: Database username
- `POSTGRES_PASSWORD`: Database password  
- `POSTGRES_DB`: Database name
- `POSTGRES_HOST`: Database host (usually 'db' for Docker)
- `POSTGRES_PORT`: Database port (usually 5432)

### Prerequisites
- Docker with PostgreSQL container running
- Database container named 'db' (as per docker-compose.yml)
- Bash shell (available on Windows via Git Bash or WSL)

## Troubleshooting

### Common Issues

1. **"Cannot connect to database"**
   - Ensure PostgreSQL container is running: `docker-compose up -d db`
   - Check if container is named 'db': `docker ps`

2. **"Missing required environment variables"**
   - Verify `.env` file exists in project root
   - Check environment variable names match those in `envexample`

3. **"SQL file not found"**
   - Run scripts from the `scripts/sql_util` directory
   - Use relative paths: `./run_sql.sh articles_today.sql`

4. **Permission denied (Linux/Mac)**
   - Make script executable: `chmod +x run_sql.sh`

### Tips
- Use `-h` or `--help` flag for usage information: `./run_sql.sh --help`
- Press `Ctrl+C` to exit interactive mode
- Use `\q` to quit from PostgreSQL interactive session
- Query results are automatically paginated for large datasets

## Custom Queries

In interactive mode, you can run custom SQL queries:

```sql
-- Example: Find articles by specific source
SELECT title, published_date, sentiment_score 
FROM article 
WHERE source = 'ESPN' 
  AND is_deleted = false 
ORDER BY published_date DESC 
LIMIT 10;

-- Example: Check processing bottlenecks
SELECT embedding_status, COUNT(*) 
FROM article 
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY embedding_status;
``` 