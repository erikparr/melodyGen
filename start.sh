#!/bin/bash

# MelodyGen Startup Script
# Starts both backend and frontend servers

echo "🎵 Starting MelodyGen..."
echo ""

# Check if we're in the right directory
if [ ! -d "src/backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the melodyGen root directory"
    exit 1
fi

# Start backend
echo "🚀 Starting backend server (FastAPI on port 8000)..."
cd src/backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 2

# Start frontend
echo "🚀 Starting frontend server (Vite on port 5173)..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
sleep 3

echo ""
echo "✅ MelodyGen is running!"
echo ""
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Trap Ctrl+C and kill both processes
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Wait for both processes
wait
