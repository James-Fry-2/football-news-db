#!/bin/bash

echo "🔄 Updating Premier League data..."
docker run --rm \
    --network football-news-db_app-network \
    --env-file .env \
    -e POSTGRES_HOST=db \
    football-news-scraper \
    python src/scripts/update_premier_league_data.py 