from dotenv import load_dotenv
import os

# Load environment variables from .env file
# Must be called before any os.getenv() calls
load_dotenv()

# OpenAI Configuration
# Strip whitespace to prevent issues with trailing newlines/spaces in .env
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '').strip() or None
# Use correct model name for Responses API
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4o-mini-2024-07-18').strip()

# Feature flags
ENABLE_LLM = os.getenv('ENABLE_LLM', 'true').lower() == 'true'

# LLM Settings
LLM_TIMEOUT = 10  # seconds
MAX_RETRIES = 2
