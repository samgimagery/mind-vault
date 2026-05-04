# Mind Vault Loading System

Mind Vault should let Sam open any Obsidian vault without explaining which one it is first.

The loader’s job is to scan once, learn the vault’s structure, create a fast visual index, and then open the graph from that prepared data.

## Principle

Obsidian remains the source of truth.

Mind Vault does **not** rewrite notes, rename files, move folders, or inject generated content into the vault by default.

Instead it creates a learned cache:

```text
<vault>/.mind-vault/
  manifest.json
  index.json
  clusters.json
  diagnostics.json
  summaries.json        # later / optional
```

This cache is rebuildable. If it is deleted, Mind Vault can scan the vault again.

## Folder Selection Flow

1. User selects an Obsidian vault folder at the start screen.
2. Mind Vault scans the folder.
3. Technical junk is ignored.
4. Markdown/text notes are accepted.
5. Structure is extracted.
6. Main nodes are created.
7. Diagnostics are shown internally.
8. The graph opens from the prepared index.

The user should not need to tell Alfred or the app which vault it is.

## Global Ignore Rules

Always ignore:

- `.obsidian`
- `.smart-env`
- `.git`
- `node_modules`
- `.mind-vault`

Do not globally ignore `Archive`, `Reference`, or other ordinary folders. In a personal or company vault those may be real content.

Mission Control is special and may keep its own operational filter:

- `Alfred`
- `Archive`
- `memory`

## Index Contents

`index.json` should contain:

- accepted notes
- stable note IDs
- paths
- names / display labels
- categories from top folders
- frontmatter summary
- tags
- outgoing `[[wikilinks]]`
- resolved links
- unresolved links
- connection counts
- inferred main nodes
- media references
- modified timestamps

Note bodies may be cached selectively, but the graph should not need full body text to open.

## Main Nodes

Main nodes should be created before opening the graph.

First pass:

- root node
- top folder/category nodes
- tag hubs
- MOC/index notes
- high-degree linked notes

Later pass:

- Gemma-generated cluster labels
- theme hubs
- dashboard cards
- “what is in this vault?” summary

## Diagnostics

The loader should record:

- files scanned
- notes accepted
- files skipped
- skip reasons
- folders discovered
- links parsed
- links resolved
- links unresolved
- visual nodes built
- drawable nodes after reveal
- timing per step

This is essential for large vaults. If a vault opens blank, diagnostics should say whether the failure is scan, index, graph build, reveal, or rendering.

## Large Vault Rules

For 800+ note vaults:

- do not rely on expensive pairwise graph physics
- open category-first
- reveal nodes in buckets, not one huge delay chain
- make search usable immediately
- allow graph to keep refining after first paint
- keep content lazy-loaded

The graph should never appear empty just because the full layout is still preparing.

## Future LLM Pass

After the structural index works, Mind Vault can run optional local LLM passes:

- node summaries
- cluster names
- dashboard overview
- presentation outline
- suggested entry points

Use Gemma for fast note-level summaries. Use larger models only where structure or quality requires it.

LLM output belongs in `.mind-vault/` cache unless Sam explicitly asks to write it back into Obsidian notes.
