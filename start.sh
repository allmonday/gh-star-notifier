#!/bin/bash

echo "🚀 Starting GitHub Star Notifier..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please edit it with your configuration."
    echo ""
    echo "📝 Required configuration:"
    echo "   - VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY (or let the app generate them)"
    echo "   - WEBHOOK_SECRET (generate with: openssl rand -hex 32)"
    echo "   - WEBHOOK_WHITELIST (e.g., [\"owner/repo\"])"
    echo ""
    echo "Press Enter to continue or Ctrl+C to edit .env first..."
    read
fi

# Start Docker Compose
echo "🐳 Starting Docker container (this will take a few minutes on first run)..."
docker-compose up -d

echo ""
echo "✅ Application started!"
echo ""
echo "📍 URLs:"
echo "   - Application: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop application:"
echo "   docker-compose down"
echo ""
