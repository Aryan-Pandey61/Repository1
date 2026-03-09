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

### Start the web server

```bash
python app.py
```

Then open <http://localhost:5000> in your browser, enter any URL, and click
**Visualize**.

---

## Deployment

### Deploy to Render

1. Fork / push this repository to your GitHub account.
2. Go to <https://render.com> and create a **New Web Service**.
3. Connect your GitHub repo — Render will auto-detect `render.yaml` and
   pre-fill all settings.
4. Click **Create Web Service**.  Your app will be live at
   `https://website-visualizer.onrender.com` (or a similar auto-generated URL).

### Deploy with Docker

```bash
# Build the image
docker build -t website-visualizer .

# Run the container
docker run -p 8080:8080 website-visualizer
```

Then open <http://localhost:8080>.

---

## CLI Usage (offline)

```bash
# Pass URL as an argument
python website_visualizer.py https://example.com

# Or run interactively
python website_visualizer.py
```

The graph is saved as `website_structure.png` in the current directory.