#!/bin/bash
cd /Users/modvader/Documents/codebase/truematchAI/backend
/Users/modvader/Documents/codebase/truematchAI/venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
