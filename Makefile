SHELL := /bin/bash
.PHONY: install bot clean bot-kill

bot:
	@export PYTHONPATH=./ && \
	python app/main.py > bot.log 2>&1 & echo $$! > bot.pid

bot-kill:
	@if [ -f bot.pid ]; then \
		kill -9 `cat bot.pid` && rm bot.pid; \
	else \
		echo "No bot.pid file found"; \
	fi

install:
	pip install -r requirements.txt

clean:
	find . -name "*.pyc" -exec rm -f {} \;
