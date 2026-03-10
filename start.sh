#!/bin/bash
cd backend
pip install -r requirements.txt
python init_db.py
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000