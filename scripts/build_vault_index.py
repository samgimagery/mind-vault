#!/usr/bin/env python3
"""Build Mind Vault's graph-first vault index.

The index is intentionally structural: notes, paths, folders, tags, frontmatter,
wikilinks, backlinks, media references, and graph stats. It does not summarize
or embed note bodies. Content stays lazy/on demand.
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_VAULT = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/Mission Control"
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "data" / "vault-index.json"
EXCLUDE_DIRS = {".git", ".obsidian", ".smart-env", "Archive", "memory", "Alfred"}
EXCLUDE_NAMES = {"MEMORY.md", "AGENTS.md", "SOUL.md", "IDENTITY.md", "USER.md", "TOOLS.md", "HEARTBEAT.md", "BOOTSTRAP.md"}
MD_EXTS = {".md", ".txt"}
MEDIA_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".mp4", ".mov", ".m4v", ".mp3", ".wav", ".m4a", ".pdf"}
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
TAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_/-]+)")
MEDIA_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
FRONTMATTER_RE = re.compile(r"^---\s*\n([\s\S]*?)\n---\s*\n?", re.MULTILINE)


def note_stem(name: str) -> str:
    return Path(name.split("#", 1)[0].split("|", 1)[0]).stem.strip()


def should_skip(path: Path, vault: Path) -> bool:
    rel = path.relative_to(vault)
    if path.name in EXCLUDE_NAMES or path.name.endswith("-Boot.md"):
        return True
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip().strip('"\'')
    return data


def main() -> int:
    vault = Path(os.environ.get("MIND_VAULT_PATH", sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VAULT)).expanduser()
    out = Path(os.environ.get("MIND_VAULT_INDEX", sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT)).expanduser()
    if not vault.exists():
        print(f"Vault not found: {vault}", file=sys.stderr)
        return 2

    notes = []
    media = []
    name_to_id = {}
    stem_to_ids = defaultdict(list)

    files = sorted(vault.rglob("*"), key=lambda p: str(p.relative_to(vault)).lower())
    for p in files:
        if not p.is_file() or should_skip(p, vault):
            continue
        rel = p.relative_to(vault).as_posix()
        if p.suffix.lower() in MEDIA_EXTS:
            media.append({"path": rel, "name": p.name, "ext": p.suffix.lower(), "category": rel.split("/", 1)[0] if "/" in rel else "Root"})
            continue
        if p.suffix.lower() not in MD_EXTS:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            text = ""
        fm = parse_frontmatter(text)
        title = p.stem
        category = rel.split("/", 1)[0] if "/" in rel else "Root"
        tags = sorted(set(TAG_RE.findall(text)))
        links = [note_stem(x) for x in WIKILINK_RE.findall(text)]
        media_refs = [m for m in MEDIA_RE.findall(text) if Path(m.split("?", 1)[0]).suffix.lower() in MEDIA_EXTS]
        stat = p.stat()
        note = {
            "id": len(notes),
            "title": title,
            "path": rel,
            "category": category,
            "tags": tags,
            "frontmatter": fm,
            "links": links,
            "backlinks": [],
            "media": media_refs,
            "size": stat.st_size,
            "mtime": int(stat.st_mtime),
        }
        notes.append(note)
        name_to_id[title] = note["id"]
        stem_to_ids[note_stem(title)].append(note["id"])
        stem_to_ids[note_stem(rel)].append(note["id"])

    edges = []
    edge_seen = set()
    for note in notes:
        for target in note["links"]:
            target_ids = stem_to_ids.get(note_stem(target), [])
            if not target_ids:
                continue
            target_id = target_ids[0]
            if target_id == note["id"]:
                continue
            key = (note["id"], target_id)
            if key in edge_seen:
                continue
            edge_seen.add(key)
            edges.append({"source": note["id"], "target": target_id, "kind": "wikilink"})
            notes[target_id]["backlinks"].append(note["title"])

    cat_counts = Counter(n["category"] for n in notes)
    tag_counts = Counter(tag for n in notes for tag in n["tags"])
    degree = Counter()
    for e in edges:
        degree[e["source"]] += 1
        degree[e["target"]] += 1
    for n in notes:
        n["degree"] = degree[n["id"]]
        n["backlinkCount"] = len(n["backlinks"])
        n["linkCount"] = len(n["links"])

    index = {
        "schema": "mind-vault-index.v1",
        "vault": str(vault),
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "notes": len(notes),
            "edges": len(edges),
            "categories": len(cat_counts),
            "tags": len(tag_counts),
            "media": len(media),
        },
        "categories": [{"name": k, "count": v} for k, v in cat_counts.most_common()],
        "tags": [{"name": k, "count": v} for k, v in tag_counts.most_common(250)],
        "topConnected": sorted(
            [{"title": n["title"], "path": n["path"], "degree": n["degree"]} for n in notes],
            key=lambda x: x["degree"],
            reverse=True,
        )[:100],
        "notes": notes,
        "edges": edges,
        "media": media,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(out)
    print(f"Wrote {out} ({len(notes)} notes, {len(edges)} edges, {len(media)} media refs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
