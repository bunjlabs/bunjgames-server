#!/usr/bin/env bash

echo "Sleeping for 5 seconds…"
sleep 5

echo "Migrate database"
python3 manage.py migrate --noinput

echo "Run server"
daphne -b 0.0.0.0 -p 8000 bunjgames_server.asgi:application
