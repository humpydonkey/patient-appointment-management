#!/bin/bash

# Demo script for Patient Appointment Management System
set -e

echo "🏥 Patient Appointment Management - Demo Setup"
echo "================================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Creating from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your OPENAI_API_KEY before proceeding"
    echo "   Then run this script again."
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  Please add your OPENAI_API_KEY to .env file"
    echo "   Edit .env and replace 'your_openai_api_key_here' with your actual key"
    exit 1
fi

echo "✅ Environment configured"

# Install backend dependencies
echo "📦 Installing backend dependencies..."
uv sync

# Install frontend dependencies if not already installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend
    pnpm install
    cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

# Run tests
echo "🧪 Running tests..."
uv run pytest tests/ -v

echo ""
echo "✅ Setup complete! Ready to run the demo."
echo ""
echo "To start the full system:"
echo "  1. Backend:  uv run python -m app.main"
echo "  2. Frontend: cd frontend && pnpm start"
echo "  3. Open:     http://localhost:3000"
echo ""
echo "Test credentials:"
echo "  • Phone: (415) 555-0123"
echo "  • DOB:   07/14/1985"
echo "  • Name:  John Adam Doe"
echo ""
echo "Quick test conversation:"
echo "  1. 'Hello, I need help with my appointments'"
echo "  2. 'My phone is (415) 555-0123 and DOB is 07/14/1985'"
echo "  3. 'Yes, that's me'"
echo "  4. 'List my appointments'"
echo "  5. 'Confirm #1'"
echo ""
echo "🎉 Happy testing!"