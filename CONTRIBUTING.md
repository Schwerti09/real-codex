# Contributing to Real Codex

## How to Contribute
1. Fork the repository and create a feature branch.
2. Follow PEP 8 coding style and add tests in `tests/`.
3. Install pre-commit hooks with `pre-commit install` to run `black`, `ruff` and `isort` automatically.
4. Submit a pull request with a clear description.
5. Ensure tests pass: `pytest -q`.
6. Update `README.md` if needed.

## Development Setup
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `pytest tests/`
- Start API: `uvicorn bioreactor_network_optimization:app --host 0.0.0.0 --port 8000`

## Issues
- Report bugs or features in GitHub Issues using the provided templates.
