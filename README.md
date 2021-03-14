# Opening Explorer

A Utility for analyzing and exploring chess opening positions.

## Installation

To get started using Python3, run:

    python -m venv .venv
    .venv\Scripts\Activate.ps1 # Assuming powershell
    pip install -r requirements.txt

This will install all the dependencies necessary to run the explorer. Running the program once will generate the settings file:

    python -m opex

Alternatively, copy `opex-default-settings.json` and rename it to `opex-settings.json`. Point that file at your UCI engine, and run again to generate `engines/<nickname>.uci`, which will contain default engine settings.

## Contributing

### Setup

To install all development dependencies run:

    pip install -r requirements/requirements-all.txt

### Testing
To run tests with coverage and report findings:

    coverage run
    coverage report

To run unittest without coverage:

    python -m unittest discover -v -s ./test -p test_*.py
