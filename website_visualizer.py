"""
Website Structure Visualizer
-----------------------------
Scrapes all internal links from a given homepage URL and displays them
as a 2D node graph (homepage = center, links = branches) using NetworkX
and matplotlib.

Usage:
    python website_visualizer.py

Requires Python 3.8+.
"""

from __future__ import annotations

import sys
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend (change to "TkAgg" or "Qt5Agg" for a window)
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import networkx as nx
import requests
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def fetch_page(url: str, timeout: int = 10) -> Optional[str]:
    """Fetch the HTML content of *url*.  Returns None on any error."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (compatible; WebVisualizer/1.0)"}
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        print(f"[ERROR] Could not fetch {url!r}: {exc}", file=sys.stderr)
        return None


def get_internal_links(homepage_url: str, html: str) -> List[str]:
    """Parse *html* and return a deduplicated list of internal links."""
    parsed_home = urlparse(homepage_url)
    base = f"{parsed_home.scheme}://{parsed_home.netloc}"

    soup = BeautifulSoup(html, "html.parser")
    seen: set = set()
    links: List[str] = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        # Skip anchors, javascript, and mailto links
        if href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(base, href)
        parsed = urlparse(full_url)

        # Keep only same-domain links and strip fragments / query strings
        if parsed.netloc == parsed_home.netloc:
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            if clean and clean != homepage_url.rstrip("/") and clean not in seen:
                seen.add(clean)
                links.append(clean)

    return links


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(homepage_url: str, internal_links: List[str]) -> nx.DiGraph:
    """Build a directed graph with *homepage_url* as the root node."""
    graph = nx.DiGraph()
    graph.add_node(homepage_url)
    for link in internal_links:
        graph.add_node(link)
        graph.add_edge(homepage_url, link)
    return graph


# ---------------------------------------------------------------------------
# Visualizer
# ---------------------------------------------------------------------------

def shorten_label(url: str, max_len: int = 35) -> str:
    """Return a shortened, human-readable label for *url*."""
    label = url.replace("https://", "").replace("http://", "")
    return label if len(label) <= max_len else label[:max_len - 1] + "…"


def visualize(graph: nx.DiGraph, homepage_url: str, output_file: str = "website_structure.png") -> None:
    """Render the graph with the homepage at the centre and save / show it."""
    num_nodes = graph.number_of_nodes()

    # --- layout ---------------------------------------------------------
    # Spring layout gives an organic "web" look; shell layout keeps the
    # homepage centred when there are enough nodes.
    if num_nodes <= 2:
        pos = nx.spring_layout(graph, seed=42)
    else:
        # Put homepage in the inner shell, everything else in the outer shell
        pos = nx.shell_layout(graph, nlist=[[homepage_url], list(graph.nodes - {homepage_url})])

    # --- figure ---------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 12))
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")
    ax.set_title(
        f"Website Structure: {shorten_label(homepage_url, 60)}",
        color="white", fontsize=14, pad=14,
    )

    # --- node styling ---------------------------------------------------
    node_colors = []
    node_sizes = []
    for node in graph.nodes:
        if node == homepage_url:
            node_colors.append("#ff6b6b")   # red-ish for homepage
            node_sizes.append(1800)
        else:
            node_colors.append("#4ecdc4")   # teal for child pages
            node_sizes.append(700)

    # --- draw nodes & edges --------------------------------------------
    nx.draw_networkx_nodes(
        graph, pos, ax=ax,
        node_color=node_colors, node_size=node_sizes,
        alpha=0.92,
    )
    nx.draw_networkx_edges(
        graph, pos, ax=ax,
        edge_color="#aaaaaa", arrows=True,
        arrowstyle="-|>", arrowsize=15,
        width=1.2, alpha=0.7,
        connectionstyle="arc3,rad=0.08",
    )

    # --- labels ---------------------------------------------------------
    labels = {node: shorten_label(node) for node in graph.nodes}
    nx.draw_networkx_labels(
        graph, pos, labels=labels, ax=ax,
        font_size=7, font_color="white", font_weight="bold",
    )

    # --- legend ---------------------------------------------------------
    legend_elements = [
        Patch(facecolor="#ff6b6b", label="Homepage"),
        Patch(facecolor="#4ecdc4", label="Internal link"),
    ]
    ax.legend(handles=legend_elements, loc="upper left",
              facecolor="#1c2128", edgecolor="gray", labelcolor="white",
              fontsize=9)

    ax.axis("off")
    plt.tight_layout()

    # Save to file (always) and optionally show in a window
    plt.savefig(output_file, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"[INFO] Graph saved to '{output_file}'")
    try:
        plt.show()
    except Exception:
        pass  # headless environment — file output is enough


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Accept URL from CLI argument or prompt the user
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("Enter the URL to visualize (e.g. https://example.com): ").strip()

    if not url:
        print("[ERROR] No URL provided.", file=sys.stderr)
        sys.exit(1)

    # Normalise: ensure scheme is present
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    print(f"[INFO] Fetching {url} …")
    html = fetch_page(url)
    if html is None:
        sys.exit(1)

    links = get_internal_links(url, html)
    print(f"[INFO] Found {len(links)} internal link(s).")

    if not links:
        print("[WARN] No internal links found. The graph will only show the homepage node.")

    graph = build_graph(url, links)
    print(f"[INFO] Building graph with {graph.number_of_nodes()} node(s) and {graph.number_of_edges()} edge(s) …")

    visualize(graph, url)


if __name__ == "__main__":
    main()
