# Opening Explorer

A utility for analyzing and exploring chess opening positions.

## Installation

### Getting started using Python3

    python -m venv .venv
    .venv\Scripts\Activate.ps1 # Assuming powershell
    pip install -r requirements.txt

This will install all the dependencies necessary to run the explorer.

### Launching opex

Running the program once will generate the settings file.

    python -m opex

Alternatively, copy `opex-default-settings.json` and rename it to `opex-settings.json`. 

The explorer will not work without a UCI compliant chess engine.Edit the settings file to reference a UCI engine, and run `opex` again.

For each engine in the settings file `opex` will generate an engine options file named `engines/<nickname>.uci`. This file can be edited to include engine options other than the default.

## Contributing

### Setup

Installing all development dependencies

    pip install -r requirements/requirements-all.txt

### Testing

Running tests with coverage and reporting findings

    coverage run
    coverage report

Running unittest without coverage

    python -m unittest discover -v -s ./test -p test_*.py
