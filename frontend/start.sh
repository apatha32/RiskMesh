#!/bin/bash

# RiskMesh Dashboard Quick Start Script

echo "🚀 RiskMesh Dashboard Setup"
echo "=============================="
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js (which includes npm)."
    echo "   Visit: https://nodejs.org/"
    exit 1
fi

echo "✓ npm found: $(npm --version)"
echo ""

# Navigate to frontend directory
cd "$(dirname "$0")" || exit

echo "📦 Installing dependencies..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ npm install failed"
    exit 1
fi

echo "✓ Dependencies installed"
echo ""

echo "🎨 Building assets..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed"
    exit 1
fi

echo "✓ Build successful"
echo ""

echo "🌐 Starting development server..."
echo "   Dashboard will open at: http://localhost:3000"
echo "   Press Ctrl+C to stop"
echo ""

npm run dev
