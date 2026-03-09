# Website Structure Visualizer

A web app that scrapes all internal links from any URL and displays them as an
interactive node graph.  Enter a URL → get a PNG graph back in your browser.

---

## Live Demo

Deploy in one click on **Render.com** (free tier) — see [Deploy to Render](#deploy-to-render) below.

---

## Running Locally

### Prerequisites

- Python 3.8+

### Setup

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
