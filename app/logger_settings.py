import logging
import sys
from env_settings import env
# Configure logging
logging.basicConfig(
    level=getattr(logging, env.LOG_LEVEL.upper(), logging.ERROR),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]  # Важно: stdout, а не stderr
)
logger = logging.getLogger(__name__)