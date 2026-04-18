"""Production WSGI entry point."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from toolkit import create_app

app = create_app(os.getenv('FLASK_CONFIG', 'production'))