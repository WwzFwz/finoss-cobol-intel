.PHONY: lint test test-cov bench build serve-api docker clean

lint:
	ruff check src/ tests/
	tach check

test:
	pytest tests/ -x -q --tb=short

test-cov:
	pytest tests/ --cov=src/cobol_intel --cov-report=term-missing

bench:
	python tools/benchmark.py

build:
	python -m build

serve-api:
	python -m uvicorn cobol_intel.api.app:app --host 0.0.0.0 --port 8000 --reload

docker:
	docker build -t cobol-intel .

clean:
	python -c "from pathlib import Path; import shutil; [shutil.rmtree(p, ignore_errors=True) for p in [Path('dist'), Path('build'), Path('.cobol_intel_cache')]]; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').rglob('__pycache__') if p.is_dir()]; [shutil.rmtree(p, ignore_errors=True) for p in Path('.').glob('*.egg-info') if p.is_dir()]"
