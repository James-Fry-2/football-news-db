#!/bin/bash

# Test crawlers in Docker
# Usage: ./scripts/test_crawlers.sh [crawler_name] [options]

set -e

echo "🐳 Testing crawlers in Docker environment..."

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is required but not installed"
    exit 1
fi

# Default values
CRAWLER=${1:-"all"}
LIMIT=${2:-5}
EXTRA_ARGS=""

# Parse additional arguments
shift 2 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            EXTRA_ARGS="$EXTRA_ARGS --verbose"
            shift
            ;;
        --save-to-db|-s)
            EXTRA_ARGS="$EXTRA_ARGS --save-to-db"
            shift
            ;;
        --list|-l)
            EXTRA_ARGS="$EXTRA_ARGS --list"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [crawler_name] [limit] [--verbose] [--save-to-db] [--list]"
            echo "Available crawlers: bbc, ffs, goal, all"
            exit 1
            ;;
    esac
done

# Ensure database is running
echo "📦 Starting required services..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Run the crawler test
echo "🚀 Running crawler test: $CRAWLER"
docker-compose run --rm scraper python scripts/test_crawlers_docker.py $CRAWLER --limit $LIMIT $EXTRA_ARGS

echo "✅ Crawler test completed!" 