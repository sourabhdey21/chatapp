# Modern Chat Application

A modern real-time chat application built with Flask, MySQL, and WebSocket technology. The application features user authentication, real-time messaging, and a beautiful UI built with Tailwind CSS.

## Features

- User authentication (login/register)
- Real-time messaging using WebSocket
- Modern and responsive UI with Tailwind CSS
- MySQL database for data persistence
- Dockerized environment for easy deployment

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. Clone the repository:
```bash
git clone <repository-url>
cd chatapp
```

2. Start the application using Docker Compose:
```bash
docker-compose up --build
```

3. Access the application:
- Open your browser and navigate to `http://localhost:5000`
- Register a new account or login with existing credentials
- Start chatting!

## Project Structure

```
chatapp/
├── app.py              # Main Flask application
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── requirements.txt    # Python dependencies
└── templates/          # HTML templates
    ├── base.html      # Base template
    ├── index.html     # Landing page
    ├── login.html     # Login page
    ├── register.html  # Registration page
    └── chat.html      # Chat interface
```

## Environment Variables

The application uses the following environment variables (configured in docker-compose.yml):

- `MYSQL_HOST`: MySQL host (default: db)
- `MYSQL_USER`: MySQL user (default: chat_user)
- `MYSQL_PASSWORD`: MySQL password (default: chat_password)
- `MYSQL_DATABASE`: MySQL database name (default: chat_db)
- `FLASK_APP`: Flask application file (default: app.py)
- `FLASK_ENV`: Flask environment (default: development)

## Security

- Passwords are hashed using Werkzeug's security functions
- User sessions are managed securely using Flask-Login
- All database queries are parameterized to prevent SQL injection

## Contributing

Feel free to submit issues and enhancement requests!

## Database Migrations (Flask-Migrate)

If you make changes to your models (e.g., add file uploads), use Flask-Migrate to update your database schema:

1. **Initialize migrations (first time only):**
   ```sh
   docker compose exec web flask db init
   ```
2. **Generate a migration:**
   ```sh
   docker compose exec web flask db migrate -m "Describe your migration here"
   ```
3. **Apply the migration:**
   ```sh
   docker compose exec web flask db upgrade
   ```

This will keep your MySQL schema in sync with your models. 