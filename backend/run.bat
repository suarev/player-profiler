@echo off
echo Starting LENS Backend API...
echo API will be available at: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
echo.

REM Activate virtual environment if it exists
if exist "data_pipeline\venv\Scripts\activate.bat" (
    call data_pipeline\venv\Scripts\activate.bat
)

REM Run with hot reload for development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000