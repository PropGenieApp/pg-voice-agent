#!/bin/sh
set -e  # Exit on error

# Default configurations
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
RUN_PYTHON="${RUN_PYTHON:-python${PYTHON_VERSION}}"
APP_DIR="${APP_DIR:-./src}"
export PATH="$HOME/.local/bin:$PATH"

run_migrations() {
    echo "Running database migrations..."
    echo "This is a placeholder. There is no migrations at this moment"
#    cd "${APP_DIR}" || exit 1
#    ${RUN_PYTHON} -m uv run alembic upgrade head
#    cd ..
}

start_application() {
    echo "Starting the application..."
    cd "$APP_DIR"
    uv run main.py
}

main() {

    run_migrations
    start_application
}

main