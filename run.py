#!/usr/bin/env python3
"""Development server entry point."""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from toolkit import create_app, socketio

app = create_app(os.getenv('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        allow_unsafe_werkzeug=True
    )