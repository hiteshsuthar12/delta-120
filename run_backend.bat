@echo off
echo Starting Delta Exchange EMA 120 Trading Bot Backend...
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause

