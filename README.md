# Football News Database

A robust system for crawling, storing, and serving football news articles from various sources, with a focus on Premier League teams and players.

## Features

- Automated news crawling from multiple sources (BBC Sport, etc.)
- MongoDB database integration for article storage
- RESTful API for article retrieval
- Configurable crawling intervals and filters
- Support for team and player-specific news
- Modern async architecture using Python

## Prerequisites

- Python 3.8+
- MongoDB 4.4+
- Node.js 14+ (for Playwright)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/football-news-db.git
cd football-news-db
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install  # Install Playwright browsers
```

4. Create a `.env` file with your configuration:
```env
MONGODB_URL=mongodb://localhost:27017
CRAWLER_INTERVAL=3600
MAX_ARTICLES_PER_CRAWL=100
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## Project Structure

```
src/
├── crawlers/           # News crawler implementations
├── db/                 # Database models and services
│   ├── models/        # Data models
│   └── services/      # Database services
├── api/               # FastAPI application
├── config.py          # Configuration management
└── main.py           # Application entry point
```

## Environment Variables Setup

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI API settings
OPENAI_API_KEY=your-openai-api-key-here

# Pinecone settings
PINECONE_API_KEY=your-pinecone-api-key-here
PINECONE_ENVIRONMENT=your-pinecone-environment-here  # e.g., "gcp-starter"

# Vector service settings (optional, defaults shown)
VECTOR_INDEX_NAME=football-news
VECTOR_NAMESPACE=articles
VECTOR_DIMENSIONS=1536
```

Required packages:
```bash
pip install python-dotenv openai pinecone
```

## Usage

1. Start the API server:
```bash
python src/main.py
```

2. The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /articles` - List articles with optional filters
- `GET /articles/{url}` - Get a specific article
- `POST /articles` - Create a new article
- `PUT /articles/{url}` - Update an article
- `DELETE /articles/{url}` - Delete an article

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

The vector service can be initialized as follows:

```python
from src.db.services.vector_service import VectorService
from src.config.vector_config import OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_ENVIRONMENT

# In your async context
vector_service = VectorService(
    session=db_session,
    openai_api_key=OPENAI_API_KEY,
    pinecone_api_key=PINECONE_API_KEY,
    pinecone_environment=PINECONE_ENVIRONMENT
)
``` 