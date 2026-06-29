# Weeks To Live

Weeks To Live estimates a death date from a birthdate and life expectancy, then
renders the result as a compact life-in-weeks grid.

## Local Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
flask --app app.main run
```

## Docker

```bash
docker compose up --build
```

The app listens on port `5000` inside the container and maps to host port `5027`
by default.

