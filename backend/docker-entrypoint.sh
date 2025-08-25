#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database..."
until nc -z -v -w30 $POSTGRES_HOST $POSTGRES_PORT; do
  echo "Waiting for database connection..."
  sleep 5
done
echo "Database is up and running!"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start the application
exec "$@"
