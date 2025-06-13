#!/bin/bash
# Simple SQL Utility Script
# Executes SQL files using: docker exec -it football-news-db-db-1 psql -U app_writer -d footbal-db

set -e  # Exit on any error

# Function to show usage
show_usage() {
    echo "Usage: $0 [SQL_FILE]"
    echo ""
    echo "Examples:"
    echo "  $0                    # Interactive mode"
    echo "  $0 query.sql          # Execute SQL file"
    echo ""
    echo "This script runs: docker exec -it football-news-db-db-1 psql -U app_writer -d footbal-db"
}

# Main script logic
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

if [ $# -eq 0 ]; then
    # No arguments - enter interactive mode
    echo "Entering interactive PostgreSQL mode..."
    docker exec -it football-news-db-db-1 psql -U app_writer -d footbal-db
elif [ $# -eq 1 ]; then
    # One argument - SQL file path
    sql_file="$1"
    
    if [ -f "$sql_file" ]; then
        echo "Executing SQL file: $sql_file"
        docker exec -i football-news-db-db-1 psql -U app_writer -d footbal-db < "$sql_file"
    else
        echo "Error: SQL file not found: $sql_file"
        exit 1
    fi
else
    echo "Error: Too many arguments"
    show_usage
    exit 1
fi 