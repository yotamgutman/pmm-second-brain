"""
Parse the Obsidian vault into chunks suitable for embedding.

Each markdown file is split into chunks along its H2 ("## ") headings.
Frontmatter (YAML) is parsed for metadata such as tags, and
[[wikilinks]] are extracted into a `related` field while being
flattened to plain text in the chunk body (so embeddings aren't
polluted with Obsidian-specific syntax).
"""

import re
from pathlib import Path

import yaml

VAULT_DIR = Path(__file__).resolve().parent.parent / "vault"

# Navigation/index pages — not retrieval content
SKIP_FILENAMES = {"Home.md", "README.md"}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _split_frontmatter(raw: str):
    match = FRONTMATTER_RE.match(raw)
    if not match:
        return {}, raw
    fm_text, body = match.groups()
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, body


def _extract_links(text: str):
    return sorted(set(WIKILINK_RE.findall(text)))


def _flatten_links(text: str) -> str:
    """Replace [[target]] / [[target|alias]] with plain target text."""
    return WIKILINK_RE.sub(lambda m: m.group(1), text)


def _chunk_by_headings(body: str):
    """
    Split a markdown body into (heading, text) chunks along H2 ("## ")
    headings. Content before the first H2 — typically the H1 title and
    intro — becomes its own chunk under heading "Overview".
    """
    chunks = []
    current_heading = "Overview"
    current_lines = []

    for line in body.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        chunks.append((current_heading, "\n".join(current_lines).strip()))

    return [(h, t) for h, t in chunks if t]


def _doc_type(rel_path: Path) -> str:
    """Top-level vault folder, used as a coarse document-type tag."""
    return rel_path.parts[0] if len(rel_path.parts) > 1 else "root"


def _title_from_body(body: str, fallback: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def parse_vault(vault_dir: Path = VAULT_DIR):
    """
    Walk the vault and return a list of chunk dicts:

        id        - unique chunk id, "<source>::<heading>"
        text      - chunk text (title + heading + body), ready to embed
        source    - relative path, e.g. "product/autosync-spec.md"
        doc_type  - top-level vault folder, e.g. "product", "competitive"
        title     - H1 title of the file
        heading   - H2 heading this chunk falls under
        tags      - comma-joined frontmatter tags
        related   - comma-joined [[wikilink]] targets found in this chunk
    """
    chunks = []
    for path in sorted(vault_dir.rglob("*.md")):
        if path.name in SKIP_FILENAMES:
            continue

        rel_path = path.relative_to(vault_dir)
        raw = path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(raw)
        title = _title_from_body(body, fallback=path.stem)

        tags = frontmatter.get("tags", [])
        if isinstance(tags, list):
            tags = ", ".join(str(t) for t in tags)

        for heading, text in _chunk_by_headings(body):
            related = _extract_links(text)
            flat_text = _flatten_links(text)
            slug = heading.lower().replace(" ", "-")
            chunk_id = f"{rel_path.as_posix()}::{slug}"

            chunks.append({
                "id": chunk_id,
                "text": f"{title} — {heading}\n\n{flat_text}",
                "source": rel_path.as_posix(),
                "doc_type": _doc_type(rel_path),
                "title": title,
                "heading": heading,
                "tags": tags,
                "related": ", ".join(related),
            })

    return chunks


if __name__ == "__main__":
    parsed = parse_vault()
    print(f"Parsed {len(parsed)} chunks from {VAULT_DIR}\n")
    for c in parsed:
        print(f"[{c['doc_type']:<11}] {c['source']:<45} :: {c['heading']}")
