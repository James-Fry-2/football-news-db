# Football News Database

A comprehensive system for collecting, analyzing, and serving football news data using Python, MongoDB, Docker, and AWS.

## Features

- Automated news scraping from multiple sources (BBC Sport, Sky Sports, etc.)
- Natural Language Processing for player and team identification
- Sentiment analysis of news articles
- RESTful API for accessing processed news data
- Containerized deployment with Docker
- AWS infrastructure for scalable deployment

## Prerequisites

- Python 3.9+
- Docker and Docker Compose
- MongoDB
- AWS CLI (for production deployment)

## Local Development Setup

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
pip install -r requirements/dev.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start the development environment:
```bash
docker-compose -f docker/docker-compose.yml up -d
```

## Project Structure

- `src/` - Source code
  - `etl/` - ETL pipeline components
  - `api/` - FastAPI application
  - `db/` - Database models and queries
  - `analysis/` - News analysis components
- `config/` - Configuration files
- `tests/` - Test suites
- `docker/` - Docker configuration
- `aws/` - AWS infrastructure code

## API Documentation

Once running, the API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

Run the test suite:
```bash
pytest tests/
```

## Deployment

### Local Deployment
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Production Deployment
```bash
# Set up AWS credentials
aws configure

# Deploy infrastructure
cd aws/cloudformation
./deploy.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- BBC Sport API
- Sky Sports API
- spaCy for NLP processing
- VADER Sentiment for sentiment analysis 