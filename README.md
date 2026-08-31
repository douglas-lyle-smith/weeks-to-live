# Weeks To Live

Weeks To Live estimates a death date from a birthdate and life expectancy, then
renders the result as a compact life-in-weeks grid.

The grid overlays two kinds of markers:

- **Personal Events** — your own dated life events. Positioned on the grid by
  calendar date relative to your birthdate; multi-week events span several
  week-dots. Import/export in CSV form (`date,end_date,name,timelines,details`),
  add/edit/delete, and hide/show individual records or the whole layer.
  See [`sample-personal-events.csv`](sample-personal-events.csv) for the import
  format.
- **Historical Figure Milestones** — reference milestones positioned by the age
  the figure was at the time.

Each layer has its own show/hide slider on the chart, and selecting a dot or a
card highlights its counterpart.

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

