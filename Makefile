PYTHON ?= python
PIP ?= $(PYTHON) -m pip

.PHONY: install-api install-web api-dev web-dev dev test lint config-check contracts check

install-api:
	$(PIP) install -e './apps/api[dev]'

install-web:
	cd apps/web && npm install

api-dev:
	$(PYTHON) -m uvicorn fieldshift.main:app --app-dir apps/api/src --reload --host 0.0.0.0 --port 8000

web-dev:
	cd apps/web && npm run dev

dev:
	@echo 'Run make api-dev and make web-dev in two terminals.'

test:
	PYTHONPATH=apps/api/src $(PYTHON) -m pytest apps/api/tests -q

lint:
	$(PYTHON) -m ruff check apps/api scripts
	$(PYTHON) -m ruff format --check apps/api scripts
	cd apps/web && npm run typecheck

config-check:
	$(PYTHON) scripts/validate_configs.py

contracts:
	PYTHONPATH=apps/api/src $(PYTHON) scripts/generate_openapi.py

check: test lint config-check
