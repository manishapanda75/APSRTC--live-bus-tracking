#!/bin/bash
# ═══════════════════════════════════════════════════════
# Azure App Service Startup Script — APSRTC Live v7.0
# ═══════════════════════════════════════════════════════
# This script is run by Azure App Service (Linux) on startup.
# Set this path as "Startup Command" in Azure Portal:
#   → App Service → Configuration → General Settings → Startup Command
#   → Value: startup.sh

echo "┌─────────────────────────────────────────┐"
echo "│   APSRTC Live Bus Tracking — v7.0       │"
echo "│   Starting on Azure App Service...      │"
echo "└─────────────────────────────────────────┘"

# Navigate to Backend directory
cd Backend

# Run database migration (creates tables + admin user if needed)
echo "[STARTUP] Running database migration/init..."
python init_db.py
echo "[STARTUP] Migration complete."

# Start the app with gunicorn
# We use gevent-websocket worker for better live tracking support
echo "[STARTUP] Starting Gunicorn..."
gunicorn --bind=0.0.0.0:${PORT:-8000} \
         --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker \
         --workers 2 \
         --timeout 120 \
         backend:app
