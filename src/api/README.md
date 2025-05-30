# Football News Database API

This API provides endpoints for managing football news articles, players, and analysis.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication.

## Endpoints

### Articles

#### List Articles
```http
GET /articles/
```

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100)
- `source` (string, optional): Filter by news source
- `team` (string, optional): Filter by team name
- `player` (string, optional): Filter by player name

#### Get Article by URL
```http
GET /articles/{url}
```

#### Create Article
```http
POST /articles/
```

Request Body:
```json
{
    "title": "string",
    "url": "string (URL)",
    "content": "string",
    "summary": "string (optional)",
    "published_date": "datetime",
    "source": "string",
    "author": "string (optional)",
    "status": "string (default: 'active')"
}
```

#### Update Article
```http
PUT /articles/{url}
```

Request Body: Same as Create Article, all fields optional

### Players

#### List Players
```http
GET /players/
```

Query Parameters:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100)

#### Get Player by ID
```http
GET /players/{player_id}
```

#### Create Player
```http
POST /players/
```

Request Body:
```json
{
    "name": "string"
}
```

#### Update Player
```http
PUT /players/{player_id}
```

Request Body:
```json
{
    "name": "string (optional)"
}
```

### Analysis

#### Get Statistics
```http
GET /analysis/stats
```

Response:
```json
{
    "total_articles": "integer",
    "articles_by_source": {
        "source_name": "count"
    },
    "articles_by_team": {
        "team_name": "count"
    },
    "articles_by_player": {
        "player_name": "count"
    }
}
```

## Error Responses

The API uses standard HTTP status codes:

- 200: Success
- 201: Created
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

Error Response Format:
```json
{
    "detail": "Error message"
}
```

## Rate Limiting

Currently, there are no rate limits implemented.

## Examples

### Get Latest Articles
```bash
curl -X GET "http://localhost:8000/api/v1/articles/?limit=10"
```

### Create New Article
```bash
curl -X POST "http://localhost:8000/api/v1/articles/" \
     -H "Content-Type: application/json" \
     -d '{
         "title": "New Transfer News",
         "url": "https://example.com/news/1",
         "content": "Article content...",
         "published_date": "2024-03-20T10:00:00Z",
         "source": "BBC Sport"
     }'
```

### Get Analysis Statistics
```bash
curl -X GET "http://localhost:8000/api/v1/analysis/stats"
``` 