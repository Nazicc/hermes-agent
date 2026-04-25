# Makefile for hermes-agent prerun script deployment
#
# Usage:
#   make deploy          — deploy all prerun scripts to ~/.hermes/scripts/
#   make deploy-rss      — deploy only rss_health_checker.py
#   make test-rss        — run rss_health_checker.py unit tests
#   make test            — run all cron tests
#
# Important: prerun scripts MUST live in ~/.hermes/scripts/ (scheduler path-traversal guard).
# After editing any cron/*_checker.py or cron/*_prerun.py, run: make deploy

HERMES_SCRIPTS := $(HOME)/.hermes/scripts
VENV_PYTHON := $(shell cat .python-version 2>/dev/null || echo "venv/bin/python3")

.PHONY: deploy deploy-rss test test-rss

deploy: deploy-rss

deploy-rss:
	@echo "Deploying prerun scripts to ~/.hermes/scripts/ ..."
	@for script in cron/rss_health_checker.py; do \
		if [ -f "$$script" ]; then \
			cp "$$script" "$(HERMES_SCRIPTS)/"; \
			chmod +x "$(HERMES_SCRIPTS)/$${script##*/}"; \
			echo "  ✅ $$script → $(HERMES_SCRIPTS)/$${script##*/}"; \
		fi; \
	done

test-rss:
	@echo "Running rss_health_checker tests ..."
	./venv/bin/python3 -m pytest cron/tests/test_rss_health_checker.py -v --tb=short

test:
	@echo "Running all cron tests ..."
	./venv/bin/python3 -m pytest cron/tests/ -v --tb=short
