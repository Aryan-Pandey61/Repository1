# Website Structure Visualizer

This project now includes a web-hostable version of the visualizer.

## What it does

- Accepts a homepage URL
- Scrapes internal links from that page
- Builds a directed graph of homepage -> internal links
- Renders and returns a PNG graph in the browser

## Run locally

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the web app:

```bash
python app.py
```

4. Open `http://localhost:8000`.

## Deploy on Render (recommended)

1. Push this repository to GitHub.
2. In Render, click `New +` -> `Web Service`.
3. Connect your GitHub repo and select this repository.
4. Use these settings:
	- Runtime: `Python 3`
	- Build Command: `pip install -r requirements.txt`
	- Start Command: `gunicorn app:app`
5. Click `Create Web Service`.

Render will assign a live URL once deployment completes.

## Deploy on Railway (alternative)

1. Push this repository to GitHub.
2. In Railway, click `New Project` -> `Deploy from GitHub repo`.
3. Select this repository.
4. Railway will install dependencies and use `Procfile` (`web: gunicorn app:app`).
5. Open the generated public domain from project settings.

## Optional: Keep CLI mode

You can still run the original script directly:

```bash
python website_visualizer.py https://example.com
```