@echo off
echo ====================================
echo   MDC Career Path Advisor - Setup
echo ====================================
echo.

echo [1/2] Setting up Backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo Backend setup complete!
echo.

echo [2/2] Setting up Frontend...
cd ..
call npm install
echo Frontend setup complete!
echo.

echo ====================================
echo   Setup Complete!
echo ====================================
echo.
echo To start the application:
echo 1. Run: start-backend.bat (in one terminal)
echo 2. Run: start-frontend.bat (in another terminal)
echo 3. Open: http://localhost:5173
echo.
pause
