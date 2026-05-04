# Mind Vault

Mind Vault is a local-first visual knowledge instrument.

It is **not** a chatbot with a graph attached. The vault graph is the brain. The assistant is only the interpreter/operator. The answer surface is visual: nodes, links, panels, decks, generated pages, media, comparisons, and stats.

## Current Product Rule

**LLM Wiki first. Content second. LLM last.**

Mind Vault should use the structure of the vault before asking any model to read or generate:

- folders / categories
- frontmatter
- tags
- `[[wikilinks]]`
- backlinks
- media references
- connection counts
- modified times
- graph stats

Note bodies stay lazy-loaded. They are only read when the user opens a note, asks to read/summarise it, generates a deck/page, or needs references.

## Current Local Flow

1. Open Mind Vault.
2. Select or load a vault.
3. Mind Vault scans/indexes the vault if needed.
4. One root node appears.
5. Click the root node.
6. The vault blooms from the root.
7. The bottom line appears with a live caret.
8. `Mind` activates local listening mode.
9. Spoken text appears in the bottom bar, then routes through the same command path as typed text.
10. The vault responds visually: focus, panel, stats, count results, comparisons, Marp deck, generated page, local summary, or voice reading.

Gemini Live has been stopped/removed from the active product direction. Voice is local-only: browser/STT for commands, Gemma for summaries, Scarlett/local TTS for long-form reading, and later pre-recorded Scarlett acknowledgements for instant UI feedback.

### Scarlett Lab bridge

Mind Vault now has an internal Scarlett Lab harness:

`POST /api/scarlett-lab/ask`

This is not a product merge. Mind Vault searches the selected local vault and shows the visual trust layer; Scarlett provides the service/voice interaction style. The endpoint returns an answer plus operational trace data: vault searched, sources used, model, score, and latency.

Design note: `docs/SCARLETT_LAB.md`

## Quick Start

```bash
cd ~/AI/OpenClaw/dev/mind-vault
~/AI/OpenClaw/dev/receptionist/.venv/bin/python3 server.py
```

Open:

`http://localhost:8788/`

Public route via Tailscale Funnel:

`https://samgs-mac-studio.tail3e92a8.ts.net/`

The active LaunchAgent is:

`~/Library/LaunchAgents/com.mind-vault.server.plist`

## Vault Loading + Indexing

Mind Vault should be able to open any selected Obsidian vault without Sam needing to explain which vault it is.

The loader should scan once, learn the vault structure, write a rebuildable cache, then open from that prepared data.

Obsidian remains the source of truth. Mind Vault does **not** rewrite notes by default.

Preferred cache location per vault:

```text
<vault>/.mind-vault/
  manifest.json
  index.json
  clusters.json
  diagnostics.json
```

The index stores:

- notes
- paths
- categories
- tags
- frontmatter
- outgoing `[[wikilinks]]`
- resolved/unresolved links
- media refs
- degree / connection counts
- inferred main nodes
- graph stats
- loader diagnostics

It does **not** need summaries or embeddings for first paint. LLM-generated summaries/clusters can be added later as optional cached layers.

Full design note:

`docs/VAULT_LOADING_SYSTEM.md`

### Manual rebuild

```bash
cd ~/AI/OpenClaw/dev/mind-vault
scripts/build_vault_index.py
```

Optional custom vault/output:

```bash
MIND_VAULT_PATH="/path/to/vault" \
MIND_VAULT_INDEX="/path/to/vault-index.json" \
scripts/build_vault_index.py
```

### Daily automatic rebuild

LaunchAgent installed:

`~/Library/LaunchAgents/com.mind-vault.index.plist`

Runs daily at **04:10** and writes:

`~/AI/OpenClaw/dev/mind-vault/data/vault-index.json`

Logs:

- `/tmp/mind-vault-index.log`
- `/tmp/mind-vault-index.err`

## Current Files

- `Mind_Vault.html` — single-file UI prototype
- `scripts/build_vault_index.py` — graph-first vault index builder
- `data/vault-index.json` — generated structural index
- `docs/ARCHITECTURE.md` — product/technical architecture
- `docs/PRESENTATION_LAYER.md` — visual presentation research/direction
- `docs/VAULT_LOADING_SYSTEM.md` — robust vault loader/index design
- `docs/EDITORIAL_SURFACES.md` — unified visual style for summaries, decks, dashboards, and readers
- `docs/NEXT_PASS.md` — next implementation pass

## Design Direction

Mind Vault should feel like being inside a living library/brain:

- root node blooms into graph
- notes grow out through links and categories
- all notes should be visible as shells
- real `[[wikilinks]]` are the core system
- content previews are lazy
- panels show structure first: path, tags, connected links, counts
- presentations appear as floating surfaces
- multiple open files eventually become a 3D paper stack

## Presentation Is The Superpower

The most important output is not chat. It is presentation:

- beautiful lists
- numbers and stats
- charts
- comparisons
- timelines
- media surfaces
- summary cards
- Marp decks
- generated PDF-style pages

Mind Vault should be able to turn a request into a designed information object, not a wall of assistant text.

The shared visual system for those answer objects is documented in:

`docs/EDITORIAL_SURFACES.md`

## Deprecated / Paused

- Gemini Live voice loop is paused.
- `gemini_live_server.py` can still exist for experiments, but it is not the active product path.
- Full-vault context injection is explicitly not allowed.
- Local RAG generation with slow model summaries should not sit in the live interaction loop.
