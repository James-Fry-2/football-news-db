# src/tasks/celery_app.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

redis_url = os.getenv('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery(
    'football_news',
    broker=redis_url,        # ← Redis as message broker
    backend=redis_url,       # ← Redis as result backend
    include=['src.tasks.vector_tasks']
)