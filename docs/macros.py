from __future__ import annotations

import re

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from mkdocs_macros.plugin import MacrosPlugin


RE_SITE_LINK = re.compile(r'\b(src|href)="https://austrosim\.readthedocs\.io/en/latest/?(.*?)"')


def on_post_build(env: MacrosPlugin) -> None:
    # Macro to replace every reference in links and images of the main website to relative ones.
    # This is especially important for docs/index.md, as it holds a reference to README.md, the main "noise" generator.
    # If required, I will narrow down this macro execution to docs/index.md
    site_dir = Path(env.conf["site_dir"])

    def mk_rel_path(file: Path) -> str:
        parts = file.parent.relative_to(site_dir).parts
        if len(parts) == 0:
            return "./"
        else:
            return "../" * len(parts)

    site_pages = (p for p in site_dir.rglob("*.html"))
    for p in site_pages:
        rel_path = mk_rel_path(p)
        patched_html = RE_SITE_LINK.sub(rf'\1="{rel_path}\2"', p.read_text())
        p.write_text(patched_html)
