#!/bin/bash
# Azure App Service startup command for APSRTC (Flask/Gunicorn)
# Set this as the Startup Command in: App Service → Configuration → General Settings
#
# Startup Command to paste in Azure Portal:
#   gunicorn --bind=0.0.0.0:$PORT --timeout 600 --workers 2 --threads 2 backend:app

gunicorn --bind=0.0.0.0:${PORT:-8000} \
         --timeout 600 \
         --workers 2 \
         --threads 2 \
         --access-logfile '-' \
         --error-logfile '-' \
         backend:app
