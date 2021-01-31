# Opening Explorer

To get started using Python3, run:

    python -m venv .venv
    .venv\Scripts\Activate.ps1 # Assuming powershell
    pip install requirements.txt

This will install all the dependencies. Running the program once will generate the settings.json file:

    python opex.py

Alternatively, edit `settings.json.default` and rename to `settings.json`. Point that file at your UCI engine, and run again to generate `output_directory/<nickname>.uci`, which will contain default engine settings.