@echo off
cd /d "%~dp0"

echo Stopping ALL Streamlit servers on 8501 and 8502...
for %%P in (8501 8502) do (
  for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%P ^| findstr LISTENING') do (
    echo   Killing PID %%a on port %%P
    taskkill /F /PID %%a >nul 2>&1
  )
)

echo Clearing Python cache...
if exist __pycache__ rmdir /s /q __pycache__ 2>nul

echo.
echo Starting CineMindAI at http://localhost:8502
echo Look for header: UI 4.0  (no Marvel / DC)
echo.
py -3 -m streamlit run app.py --server.port 8502
pause
