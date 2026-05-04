# Mind Vault Architecture

## North Star

Mind Vault is a local-first visual knowledge instrument.

The graph is the brain. The assistant is the interpreter/operator. The stage is where knowledge becomes visible.

## Product Spine

1. **Vault Index** — fast structural graph
2. **Visual Brain** — nodes, links, backlinks, tags, categories, stats
3. **Stage Layer** — panels, decks, generated pages, media, comparisons
4. **Local Listener** — microphone command intake, no live chat dependency
5. **Local Voice** — small canned acknowledgements + optional document reading

## What The LLM Does Not Do

The LLM does not ingest the whole vault.
The LLM does not become the brain.
The LLM should not receive full vault context.

## What The Vault Index Does

The vault index is the core system.

It stores structural intelligence:

- note title
- path
- category/folder
- frontmatter
- tags
- outgoing `[[wikilinks]]`
- backlinks
- media references
- degree / connection counts
- modified time
- graph stats

This lets Mind Vault answer structural questions instantly:

- what is in this vault?
- what are the biggest clusters?
- which notes connect these topics?
- what changed recently?
- what has no backlinks?
- what are the strongest reference hubs?

## Runtime Loading Model

**Fast path:** load `vault-index.json`.

**Lazy path:** load note bodies only when needed:

- user opens a note
- user asks to read it
- user asks for a deck/page/PDF
- user needs source excerpts
- user asks for detail beyond graph metadata

## Large Vault Strategy

For 800–2000+ notes:

- draw all note shells
- simplify physics
- avoid all-pairs repulsion
- progressively parse/update links
- use index stats for immediate layout
- lazy-load note bodies
- cluster by real graph structure first, folder second

The solution is not to hide most nodes. The solution is to render shells cheaply and reserve expensive work for focus/context.

## Voice Direction

Gemini Live is paused. The product direction is local-first.

The local voice system should do:

- canned acknowledgements immediately
- listen for commands
- run local retrieval/index operations
- show visual output
- read documents only when asked

Examples of canned clips:

- hi
- yes
- of course
- absolutely
- one moment
- at your convenience
- no

## Interaction Model

- click `Mind Vault` — enter
- click root node — bloom graph
- bottom line appears
- click `Mind` — listen
- speak request
- vault presents visual result
- say/click `Marp` — deck appears
- say/click `discard` — close current surface
- say/click `read` — local voice reads selected document
- pin nodes for comparison

## Presentation Surfaces

Mind Vault should create designed output surfaces:

- note panel
- stats panel
- comparison board
- Marp deck
- PDF-style page
- media viewer
- timeline
- chart/dashboard
- 3D document stack

## Daily Indexing

Installed LaunchAgent:

`~/Library/LaunchAgents/com.mind-vault.index.plist`

Runs daily at 04:10.

Script:

`~/AI/OpenClaw/dev/mind-vault/scripts/build_vault_index.py`

Output:

`~/AI/OpenClaw/dev/mind-vault/data/vault-index.json`
