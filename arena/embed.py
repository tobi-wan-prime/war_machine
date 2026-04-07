"""Generate a self-contained HTML file with embedded replay data."""

from __future__ import annotations

import os


def generate_embedded_html(replay_json: str, scenario_name: str = "Custom") -> str:
    """Build a self-contained HTML string with replay data embedded."""
    viewer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "viewer.html")

    with open(viewer_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace the title
    html = html.replace(
        "<title>War Machine: Arena — Replay Viewer</title>",
        f"<title>War Machine: Arena — {scenario_name}</title>",
    )

    # Change subtitle
    html = html.replace(
        "Evolutionary Simulation Replay",
        f"Evolutionary Simulation — {scenario_name}",
    )

    # Hide load section via CSS, show viewer
    html = html.replace(
        "#viewer { display: none; }",
        "#viewer { display: block; }\n#load-section { display: none !important; }",
    )

    # Add back-to-index navigation link
    nav_html = '<div style="text-align:center;margin-bottom:6px"><a href="index.html" style="color:#ff6633;text-decoration:none;font-size:0.8em">&larr; Back to Scenario Index</a></div>'
    html = html.replace(
        '<h1>WAR MACHINE: ARENA</h1>',
        nav_html + '<h1>WAR MACHINE: ARENA</h1>',
    )

    # Inject the replay data and auto-init script before closing </script>
    auto_init_js = f"""

// === EMBEDDED REPLAY DATA ===
const EMBEDDED_DATA = {replay_json};

// Auto-initialize with embedded data
(function() {{
    replayData = EMBEDDED_DATA;
    initViewer();
}})();
"""

    html = html.replace("</script>", auto_init_js + "</script>")

    return html
