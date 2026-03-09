"""
Flask web app for the Website Structure Visualizer.

Routes
------
GET  /           — landing page with URL input form
POST /visualize  — scrape URL, render graph, return PNG inline
"""

from __future__ import annotations

import io
import ipaddress
import os
import socket
from urllib.parse import urlparse

import matplotlib
matplotlib.use("Agg")  # non-interactive, must be set before importing pyplot
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from flask import Flask, request, send_file, render_template_string

from website_visualizer import fetch_page, get_internal_links, build_graph

app = Flask(__name__)

# ---------------------------------------------------------------------------
# SSRF guard — block requests to private / reserved IP ranges
# ---------------------------------------------------------------------------

_PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _is_public_url(url: str) -> bool:
    """Return True only when *url* resolves to a public (non-private) IP."""
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
        return not any(ip in net for net in _PRIVATE_NETS)
    except Exception:
        return False

# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Website Structure Visualizer</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: Arial, sans-serif;
      background: #0d1117;
      color: #e6edf3;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 3rem 1rem;
    }
    h1 { font-size: 1.8rem; color: #4ecdc4; margin-bottom: .4rem; }
    p.sub { color: #8b949e; margin-bottom: 2rem; }
    form {
      display: flex;
      gap: .6rem;
      width: 100%;
      max-width: 600px;
      flex-wrap: wrap;
    }
    input[type=url] {
      flex: 1;
      padding: .7rem 1rem;
      border: 1px solid #30363d;
      border-radius: 6px;
      background: #161b22;
      color: #e6edf3;
      font-size: 1rem;
      outline: none;
    }
    input[type=url]:focus { border-color: #4ecdc4; }
    button {
      padding: .7rem 1.4rem;
      background: #4ecdc4;
      color: #0d1117;
      font-weight: bold;
      border: none;
      border-radius: 6px;
      cursor: pointer;
      font-size: 1rem;
    }
    button:hover { background: #38b2ab; }
    .error {
      margin-top: 1.5rem;
      padding: .9rem 1.2rem;
      background: #3d1a1a;
      border: 1px solid #ff6b6b;
      border-radius: 6px;
      color: #ff6b6b;
      max-width: 600px;
      width: 100%;
    }
    .result {
      margin-top: 2rem;
      max-width: 960px;
      width: 100%;
      text-align: center;
    }
    .result img {
      max-width: 100%;
      border-radius: 8px;
      border: 1px solid #30363d;
    }
    .result p { margin-top: .8rem; color: #8b949e; font-size: .9rem; }
  </style>
</head>
<body>
  <h1>🌐 Website Structure Visualizer</h1>
  <p class="sub">Enter a URL to map its internal link structure as a graph.</p>

  <form method="post" action="/visualize">
    <input type="url" name="url" placeholder="https://example.com"
           value="{{ url or '' }}" required autofocus />
    <button type="submit">Visualize</button>
  </form>

  {% if error %}
  <div class="error">⚠ {{ error }}</div>
  {% endif %}

  {% if img_url %}
  <div class="result">
    <img src="{{ img_url }}" alt="Website structure graph" />
    <p>Graph for <strong>{{ url }}</strong> — {{ link_count }} internal link(s) found.</p>
  </div>
  {% endif %}
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Graph rendering helper (returns PNG bytes via in-memory buffer)
# ---------------------------------------------------------------------------

def render_to_png(graph, homepage_url: str) -> io.BytesIO:
    """Render *graph* to PNG and return a seeked BytesIO buffer."""
    from website_visualizer import shorten_label

    num_nodes = graph.number_of_nodes()

    import networkx as nx
    if num_nodes <= 2:
        pos = nx.spring_layout(graph, seed=42)
    else:
        pos = nx.shell_layout(
            graph,
            nlist=[[homepage_url], list(graph.nodes - {homepage_url})],
        )

    fig, ax = plt.subplots(figsize=(16, 12))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    ax.set_title(
        f"Website Structure: {shorten_label(homepage_url, 60)}",
        color="white", fontsize=14, pad=14,
    )

    node_colors, node_sizes = [], []
    for node in graph.nodes:
        if node == homepage_url:
            node_colors.append("#ff6b6b")
            node_sizes.append(1800)
        else:
            node_colors.append("#4ecdc4")
            node_sizes.append(700)

    nx.draw_networkx_nodes(graph, pos, ax=ax,
                           node_color=node_colors, node_size=node_sizes, alpha=0.92)
    nx.draw_networkx_edges(graph, pos, ax=ax,
                           edge_color="#aaaaaa", arrows=True,
                           arrowstyle="-|>", arrowsize=15,
                           width=1.2, alpha=0.7,
                           connectionstyle="arc3,rad=0.08")

    labels = {node: shorten_label(node) for node in graph.nodes}
    nx.draw_networkx_labels(graph, pos, labels=labels, ax=ax,
                            font_size=7, font_color="white", font_weight="bold")

    legend_elements = [
        Patch(facecolor="#ff6b6b", label="Homepage"),
        Patch(facecolor="#4ecdc4", label="Internal link"),
    ]
    ax.legend(handles=legend_elements, loc="upper left",
              facecolor="#1c2128", edgecolor="gray", labelcolor="white", fontsize=9)

    ax.axis("off")
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return render_template_string(_HTML)


@app.post("/visualize")
def visualize():
    raw_url = request.form.get("url", "").strip()

    if not raw_url:
        return render_template_string(_HTML, error="Please enter a URL.")

    # Normalize scheme
    if not raw_url.startswith(("http://", "https://")):
        raw_url = "https://" + raw_url

    # Basic validation
    parsed = urlparse(raw_url)
    if not parsed.netloc:
        return render_template_string(_HTML, url=raw_url,
                                      error="Invalid URL — could not parse domain.")

    # SSRF guard: reject URLs that resolve to private/internal addresses
    if not _is_public_url(raw_url):
        return render_template_string(
            _HTML, url=raw_url,
            error="URL resolves to a private or reserved address and cannot be fetched.",
        )

    html = fetch_page(raw_url)
    if html is None:
        return render_template_string(
            _HTML, url=raw_url,
            error=f"Could not fetch '{raw_url}'. Check the URL and try again.",
        )

    links = get_internal_links(raw_url, html)
    graph = build_graph(raw_url, links)
    png_buf = render_to_png(graph, raw_url)

    # Return the PNG image directly
    return send_file(
        png_buf,
        mimetype="image/png",
        as_attachment=False,
        download_name="website_structure.png",
    )


# ---------------------------------------------------------------------------
# Entry point (dev server)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Development server only — use gunicorn for production.
    # Set FLASK_DEBUG=1 in your environment to enable debug mode.
    _debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=_debug)
