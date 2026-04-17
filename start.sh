#!/bin/bash
# =============================================
# EcoSphere — Full Stack Startup Script
# =============================================
# Usage: bash start.sh

echo ""
echo "🌿 ======================================"
echo "   EcoSphere — Circular Economy Platform"
echo "   By IA (Innovators Arena)"
echo "========================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Install from python.org"
  exit 1
fi

# Install backend deps
echo "📦 Installing backend dependencies..."
cd ecoloop-backend
pip install -r requirements.txt -q

echo ""
echo "🚀 Starting EcoSphere backend on http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo ""
echo "🌐 Frontend: Open ecoloop-frontend/index.html in browser"
echo "   OR run: python3 -m http.server 3000 in ecoloop-frontend/"
echo ""
echo "🔑 Demo credentials: techplast@ecosphere.in / ecosphere123"
echo "🤖 Add Gemini key via navbar → AI Settings"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"

python3 -m uvicorn main:app --reload --port 8000
