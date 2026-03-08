from __future__ import annotations

import base64
import os
import tempfile
from flask import Flask, request

from website_visualizer import build_graph, fetch_page, get_internal_links, visualize

app = Flask(__name__)

HTML_PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Website Structure Visualizer</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 2rem auto;
      max-width: 900px;
      padding: 0 1rem;
      color: #222;
    }
    h1 { margin-bottom: 0.5rem; }
    form { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 1rem 0 1.5rem; }
    input[type='text'] {
      flex: 1;
      min-width: 280px;
      padding: 0.65rem;
      border: 1px solid #ccc;
      border-radius: 8px;
      font-size: 1rem;
    }
    button {
      padding: 0.65rem 1rem;
      border: 0;
      border-radius: 8px;
      background: #0077cc;
      color: #fff;
      font-size: 1rem;
      cursor: pointer;
    }
    .error {
      color: #b00020;
      margin-bottom: 1rem;
      font-weight: 600;
    }
    .meta {
      margin-bottom: 1rem;
      color: #444;
    }
    img {
      width: 100%;
      border: 1px solid #ddd;
      border-radius: 10px;
    }
  </style>
</head>
<body>
  <h1>Website Structure Visualizer</h1>
  <p>Enter a homepage URL to generate an internal-link graph.</p>

  <form method="post">
    <input type="text" name="url" placeholder="https://example.com" value="{url_value}" required>
    <button type="submit">Visualize</button>
  </form>

  {error_block}
  {meta_block}
  {image_block}
</body>
</html>
"""


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


@app.route("/", methods=["GET", "POST"])
def index() -> str:
    url_value = ""
    error_block = ""
    meta_block = ""
    image_block = ""

    if request.method == "POST":
        url_value = request.form.get("url", "").strip()
        if not url_value:
            error_block = '<div class="error">Please provide a URL.</div>'
        else:
            normalized_url = _normalize_url(url_value)
            html = fetch_page(normalized_url)

            if html is None:
                error_block = (
                    '<div class="error">Could not fetch that URL. '
                    "Please verify it is reachable.</div>"
                )
            else:
                links = get_internal_links(normalized_url, html)
                graph = build_graph(normalized_url, links)

                tmp_path = ""
                try:
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                        tmp_path = tmp.name

                    visualize(graph, normalized_url, output_file=tmp_path, show_plot=False)

                    with open(tmp_path, "rb") as image_file:
                        encoded = base64.b64encode(image_file.read()).decode("ascii")

                    meta_block = (
                        f'<div class="meta">Found {len(links)} internal link(s). '
                        f"Graph has {graph.number_of_nodes()} node(s) and "
                        f"{graph.number_of_edges()} edge(s).</div>"
                    )
                    image_block = (
                        '<img alt="Website structure graph" '
                        f'src="data:image/png;base64,{encoded}">'
                    )
                except Exception:
                    error_block = (
                        '<div class="error">Something went wrong while generating '
                        "the graph.</div>"
                    )
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        os.remove(tmp_path)

    return HTML_PAGE.format(
        url_value=url_value,
        error_block=error_block,
        meta_block=meta_block,
        image_block=image_block,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
