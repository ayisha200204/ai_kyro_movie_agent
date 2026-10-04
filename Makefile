install:
	pip install -r requirements.txt

index:
	python -m core.ingest

reset-index:
	python -m core.ingest --reset

app:
	streamlit run app/streamlit_app.py

test:
	pytest -q
