.PHONY: install backend frontend test

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn api.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && python -m pytest tests/ -v

test-fast:
	cd backend && python -m pytest tests/ -v -m "not slow"
