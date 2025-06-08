#!/bin/sh
set -e

# Wait for the database to be ready
python wait_for_db.py

# Create tables
python -c "from app import db; db.create_all()"

# Start the Flask app
exec flask run --host=0.0.0.0 