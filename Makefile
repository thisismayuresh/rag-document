# Common developer commands. Run these from the repository root.
# `make` with no target prints this list.

PYTHON := .venv/bin/python

.PHONY: help install api api-reload cli frontend frontend-build typecheck check

help:
	@echo "make install         - editable install of the python package (pyproject.toml)"
	@echo "make api             - run the HTTP API on :8000"
	@echo "make api-reload      - run the HTTP API with auto-reload"
	@echo "make cli PDF=path    - terminal chat about one PDF"
	@echo "make frontend        - run the React dev server on :5173"
	@echo "make frontend-build  - typecheck + production build of the frontend"
	@echo "make typecheck       - python compile check + frontend tsc"
	@echo "make check           - everything typecheck does, plus api import check"

install:
	$(PYTHON) -m pip install -e .

api:
	$(PYTHON) -m uvicorn document_agent.api.main:app --host 127.0.0.1 --port 8000

api-reload:
	$(PYTHON) -m uvicorn document_agent.api.main:app --reload

cli:
	$(PYTHON) -m document_agent.cli $(PDF)

frontend:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

typecheck:
	$(PYTHON) -m compileall -q src
	cd frontend && npx tsc --noEmit

check: typecheck
	$(PYTHON) -c "import document_agent.api.main; print('api imports OK')"
