# CLAUDE.md - Development Guidelines

## Build and Test Commands
- Setup: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Run: `python src/main.py`
- Run Locally: `./run_local.py`
- Tests: `pytest`
- Single Test: `pytest tests/specific_test.py::test_function`
- Lint: `flake8 src tests`
- Type Check: `mypy src`

## Workflow Guidelines
- **Altijd wijzigingen testen** voordat ze worden gecommit
- **Wijzigingen eerst zelf lokaal testen** voordat om testen via Telegram wordt gevraagd
- De applicatie lokaal uitvoeren om functionaliteit te verifiëren
- Kleine, gerichte commits maken met duidelijke berichten
- API-sleutels en authenticatievereisten documenteren
- **Eerst overleggen voordat je grote wijzigingen maakt**
- In het Nederlands communiceren, tenzij de code en documentatie in het Engels is
- Uitleggen wat je idee is en om input vragen voor je het oppakt

## Code Style Guidelines
- **Python**: Follow PEP 8 style guide
- **Formatting**: 4 spaces for indentation, 88 character line limit (Black formatter)
- **Imports**: Group standard library, third-party, and local imports
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Types**: Use type annotations with mypy enforcement
- **Error Handling**: Explicit exception handling, avoid bare excepts
- **Security**: No hardcoded secrets, use environment variables
- **Architecture**: Follow clean architecture principles with clear separation of concerns
- **Modules**: Organize by feature or domain, not by technical role
- **Documentation**: Docstrings for all public functions, classes, and modules