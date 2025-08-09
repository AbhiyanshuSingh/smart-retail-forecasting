@"
install:
	pip install -r requirements.txt

run-api:
	uvicorn src.api.app:app --reload --port 8080

lint:
	black .

test:
	pytest
"@ | Out-File -FilePath "Makefile" -Encoding UTF8
