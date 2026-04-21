#!/usr/bin/env bash
cd backend || exit
python -m uvicorn main:app --host 0.0.0.0 --port 
