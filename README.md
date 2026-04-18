# Toolkit.uno

A personal ecosystem website built with Flask, MySQL, Redis, and Elasticsearch.

## Features

- **Multi-subdomain architecture**: Separate subdomains for different functionalities (www, account, settings, notice, contacts, chat)
- **Real-time chat**: WebSocket-based messaging using Flask-SocketIO
- **Contact management**: Organize and manage contacts with notes and favorites
- **Notifications**: Customizable notification system
- **User authentication**: Secure login with Flask-Login and JWT
- **Responsive design**: Modern CSS with theme support (light/dark)
- **Dockerized**: Full containerized deployment with Docker Compose

## Tech Stack

- **Backend**: Flask 2.3, Python 3.10
- **Database**: MySQL 8.0 with SQLAlchemy ORM
- **Cache/Queue**: Redis
- **Search**: Elasticsearch 8.x
- **WebSocket**: Flask-SocketIO with eventlet
- **Frontend**: Jinja2 templates, vanilla JavaScript, CSS3
- **Deployment**: Docker, Docker Compose, Nginx, Gunicorn

## Project Structure

```
toolkit-backend/
├── toolkit/                    # Main application package
│   ├── blueprints/            # Flask blueprints
│   │   ├── www/              # Main website
│   │   ├── account/          # Authentication
│   │   ├── settings/         # User settings
│   │   ├── notice/           # Notifications
│   │   ├── contacts/         # Contact management
│   │   └── chat/             # Real-time chat
│   ├── models/               # SQLAlchemy models
│   ├── static/               # Static assets
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/            # Jinja2 templates
│       ├── www/
│       ├── account/
│       ├── settings/
│       ├── notice/
│       ├── contacts/
│       ├── chat/
│       ├── errors/
│       └── includes/
├── config.py                 # Configuration classes
├── requirements.txt          # Python dependencies
├── docker-compose.yml       # Docker services
├── Dockerfile              # Web service Dockerfile
├── run.py                  # Development server
└── wsgi.py                 # Production WSGI entry point
```

## Prerequisites

- Docker and Docker Compose
- Python 3.10+ (for local development)
- MySQL client (optional)
- Redis client (optional)

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd toolkit-backend
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Update `.env` with your settings (optional for development).

4. Start all services:
   ```bash
   docker-compose up -d
   ```

5. Initialize the database:
   ```bash
   docker-compose exec web flask db upgrade
   ```

6. Create an admin user:
   ```bash
   docker-compose exec web flask create-admin
   ```

7. Access the application:
   - Website: http://localhost:5000
   - Nginx proxy: http://localhost (if using subdomains)

### Local Development

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env for local development
   ```

3. Start MySQL, Redis, and Elasticsearch:
   ```bash
   # Using Docker
   docker-compose up -d mysql redis elasticsearch
   ```

4. Initialize database:
   ```bash
   flask db upgrade
   ```

5. Create admin user:
   ```bash
   flask create-admin
   ```

6. Run development server:
   ```bash
   python run.py
   ```

## Subdomain Configuration

For local development with subdomains, add these lines to your `/etc/hosts` file:

```
127.0.0.1 www.toolkit.local
127.0.0.1 account.toolkit.local
127.0.0.1 settings.toolkit.local
127.0.0.1 notice.toolkit.local
127.0.0.1 contacts.toolkit.local
127.0.0.1 chat.toolkit.local
```

Then access the application at `http://www.toolkit.local:5000`.

## Available Commands

- `flask db upgrade` - Apply database migrations
- `flask db migrate` - Create new migration
- `flask init-db` - Initialize database tables
- `flask create-admin` - Create admin user
- `docker-compose up -d` - Start all services
- `docker-compose down` - Stop all services
- `docker-compose logs -f web` - View web service logs

## API Endpoints

### Authentication
- `GET/POST /account/login` - User login
- `GET/POST /account/register` - User registration
- `GET /account/logout` - User logout

### Contacts API
- `GET /contacts/api/contacts` - List contacts
- `POST /contacts/api/contacts` - Add contact
- `PUT /contacts/api/contacts/{id}` - Update contact
- `DELETE /contacts/api/contacts/{id}` - Delete contact

### Chat API
- `GET /chat/api/conversations` - List conversations
- `GET /chat/api/conversations/{user_id}/messages` - Get messages
- `POST /chat/api/conversations/{user_id}/messages` - Send message

### Notifications API
- `GET /notice/api/notifications` - List notifications
- `POST /notice/api/notifications/{id}/read` - Mark as read
- `POST /notice/api/notifications/read-all` - Mark all as read

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | (random) |
| `DATABASE_URL` | MySQL connection URL | `mysql+pymysql://root:password@localhost:3306/toolkit` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `ELASTICSEARCH_URL` | Elasticsearch URL | `http://localhost:9200` |
| `CORS_ORIGINS` | CORS allowed origins | `*` |

### Database Migrations

This project uses Flask-Migrate for database migrations:

```bash
# Create new migration
flask db migrate -m "Migration message"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| `web` | 5000 | Flask application (Gunicorn) |
| `mysql` | 3306 | MySQL database |
| `redis` | 6379 | Redis cache/message queue |
| `elasticsearch` | 9200, 9300 | Elasticsearch search engine |
| `nginx` | 80, 443 | Nginx reverse proxy |

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run tests
pytest
```

### Code Style

```bash
# Format code with black
black .

# Check code style with flake8
flake8
```

### Debugging

```bash
# Run with debug mode
FLASK_ENV=development python run.py

# View logs
docker-compose logs -f web
```

## Deployment

### Production Notes

1. Set strong secret keys in `.env`:
   ```bash
   SECRET_KEY=$(openssl rand -hex 32)
   WTF_CSRF_SECRET_KEY=$(openssl rand -hex 32)
   ```

2. Use HTTPS with valid SSL certificates.

3. Configure proper database backups.

4. Set up monitoring and alerting.

5. Use environment-specific configurations.

### Scaling

- Use multiple Gunicorn workers (`--workers` flag)
- Consider Redis cluster for high availability
- Use MySQL replication or cluster
- Implement Elasticsearch cluster
- Use CDN for static assets

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.