#!/bin/bash

echo "🔧 Building frontend locally..."

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build
echo "🏗️  Building..."
npm run build

echo "✅ Build complete!"
echo "📁 Output: dist/spa/"
