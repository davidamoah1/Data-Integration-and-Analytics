from __future__ import annotations

import streamlit.components.v1 as components


def register_pwa() -> None:
    components.html(
        """
        <script>
        (() => {
          const root = window.parent.document;
          const addLink = (rel, href, sizes) => {
            if (root.querySelector(`link[rel="${rel}"][href="${href}"]`)) return;
            const link = root.createElement("link");
            link.rel = rel;
            link.href = href;
            if (sizes) link.sizes = sizes;
            root.head.appendChild(link);
          };
          addLink("manifest", "/app/static/manifest.json");
          addLink("apple-touch-icon", "/app/static/icons/dataflow-192.svg", "192x192");
          if (!root.querySelector('meta[name="theme-color"]')) {
            const theme = root.createElement("meta");
            theme.name = "theme-color";
            theme.content = "#4f46e5";
            root.head.appendChild(theme);
          }
          if ("serviceWorker" in navigator) {
            navigator.serviceWorker.register("/app/static/service-worker.js").catch(() => undefined);
          }
        })();
        </script>
        """,
        height=0,
        width=0,
    )
