from redis import Redis
from rq import Queue
from dotenv import load_dotenv
import os

# Load variables from .env into environment
load_dotenv()

redis_password = os.getenv("REDIS_PASSWORD")
redis_conn = Redis(host='13.203.74.124', port=6379, password=redis_password)
task_queue = Queue("criteria_task_queue", connection=redis_conn)
redis_url = f"redis://:{redis_password}@13.203.74.124:6379/0"