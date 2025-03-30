install:
	python3.11 -m venv .venv
	. .venv/bin/activate && \
	pip install -r requirements.txt && \
	deactivate

update:
	. .venv/bin/activate && \
	python main.py && \
	deactivate
	git add .
	git commit -m "Update README.md with latest information"
	git push origin main
