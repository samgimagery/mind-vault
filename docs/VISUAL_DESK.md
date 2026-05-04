# Mind Vault Visual Desk

Mind Vault is becoming a live data exploration tool, not a chat window and not just a graph.

The core model is:

```text
Vault Node → Surface → Pinned Desk → Synthesis
```

A node is the source. A surface is a designed way of looking at that source. The desk is where useful surfaces stay visible. Synthesis is what the helper does across the visible/pinned material.

## Product Intent

Sam should be able to explore a vault visually and ask the helper to organise what is on screen.

Examples:

- “open this”
- “summarize that”
- “pin that”
- “open all pinned”
- “compare these”
- “show me figures”
- “make a deck from these”
- “what matters here?”

The UI should feel like a dark editorial instrument: spatial, calm, readable, and alive.

## Surface Types

Every thing Mind Vault opens should become a surface object.

Initial surface types:

- `document` — full Obsidian note / Markdown reader
- `deck` — Marp presentation generated from a note or summary
- `summary` — local LLM summary card
- `data` — counts, numbers, extracted stats, tables, charts
- `comparison` — analysis across two or more surfaces
- `media` — image, video, audio, PDF viewer
- `dashboard` — multi-card synthesis view

A surface is not just DOM. It is state the helper can reason over.

Suggested shape:

```js
{
  id: 'surface_...',
  type: 'document',
  title: 'Title',
  sourceNodeId: 42,
  sourcePath: 'Folder/Note.md',
  content: 'raw readable content',
  summary: 'optional generated summary',
  preview: 'short visible preview',
  media: [],
  createdAt: 1777279671667,
  updatedAt: 1777279671667
}
```

## Surface Registry

Mind Vault should maintain one registry:

```js
surfaceRegistry = {
  current: null,
  pinned: [],
  history: []
}
```

Rules:

- Opening a document/deck/summary sets `current`.
- `pin that` moves/copies `current` into `pinned`.
- `show pinned` opens the desk view.
- Synthesis commands operate on `current`, selected surfaces, or all pinned surfaces depending on context.
- History keeps recently opened surfaces so the helper can resolve “that one” and “the previous one”.

## Visual Desk

Pinned surfaces should appear as physical visual objects, not bookmarks.

First version:

- a right or lower side tray of floating cards
- each card has title, type, source, and tiny preview
- clicking a pinned card reopens it
- “show pinned” expands them into a spatial board

Desired visual language:

- thin 3D paper / glass cards
- slight tilt and depth shadow
- restrained sepia/white edge light
- cards feel placed on a visual desk, not stacked in a web sidebar
- the graph remains behind or around the desk

Later version:

- cards can be dragged around
- cards can group by source/category
- comparison lines or brackets can appear between selected cards
- data cards can be generated beside documents

## Command Model

Typed and voice commands use the same router.

Core commands:

- `pin that` → pin current surface
- `unpin that` → remove current/selected pinned surface
- `show pinned` / `open pinned` → expand desk view
- `clear pinned` → empty tray after confirmation if needed
- `summarize this` → summary surface for current node/surface
- `summarize pinned` → summary across all pinned surfaces
- `compare these` → comparison surface from selected/pinned surfaces
- `show figures` / `find numbers` → data surface
- `make deck from these` → Marp deck from pinned/synthesis surface
- `document` / `open document` → full document surface
- `deck` / `marp` → deck surface
- `close` / `dismiss` → close current visible surface

## Synthesis Flow

The helper should not analyze the whole vault blindly when Sam is exploring.

It should first use the visual context:

1. Current surface
2. Selected/pinned surfaces
3. Visible graph cluster
4. Search results
5. Full vault only when explicitly needed

This makes the assistant feel like it is looking at the same things Sam is looking at.

## Data Exploration

Mind Vault should support live questions over visible/pinned material:

- “how many?”
- “what changed?”
- “what are the top themes?”
- “which one has numbers?”
- “compare these two”
- “turn this into a one-page brief”
- “make me a deck”

Outputs should be surfaces too:

- summary card
- data card
- comparison card
- dashboard board
- Marp deck

## Media and PDFs

Images, videos, audio, and PDFs should become first-class surfaces.

Next technical step: create a local media registry from the selected folder so Markdown/Obsidian attachments resolve reliably.

Supported eventual behaviour:

- image opens as media card
- video opens as playable media card
- audio opens as player/transcript card
- PDF opens as document/extraction card
- helper can summarize/read/compare media-derived text
- decks can reference media thumbnails or extracted figures

## Implementation Order

1. Document this architecture.
2. Update Mission Control REQ-089 to include Visual Desk and pinned surfaces.
3. Implement `surfaceRegistry`.
4. Make Document, Deck, and Summary register themselves as surfaces.
5. Implement `pinCurrentSurface()` and `pin that`.
6. Add pinned tray with small floating cards.
7. Add `show pinned` board view.
8. Add synthesis commands over pinned surfaces.
9. Add media registry and PDF/media surfaces.

## Non-Goals For First Pass

Do not start with full drag/drop, rich charts, or perfect 3D.

First pass only needs:

- reliable current surface state
- reliable pinning
- visible pinned tray
- command routing
- one end-to-end test: open note → document/deck/summary → pin → show pinned

Get the spine right first. The spectacle can grow from it.
