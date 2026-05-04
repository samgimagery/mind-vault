# Mind Vault Editorial Surfaces

Mind Vault should not feel like chat output pasted onto a graph.

When Mind Vault answers, it should create an editorial object: a designed surface that can be read, dismissed, spoken, turned into Marp, pinned to the Visual Desk, or reused as a dashboard card.

Related architecture: `docs/VISUAL_DESK.md`.

## Product Model

```text
Vault Node → Surface → Pinned Desk → Synthesis
```

A surface is a visual/readable object. It is also structured state the helper can reason over.

## Surfaces

The main answer surfaces are:

- Document reader
- Summary card
- Count/stat card
- Comparison card
- Marp deck overlay
- Media/PDF viewer
- Dashboard board

All should share one visual language.

## Editorial Style

Tone: calm, precise, premium, dark, readable.

Visual rules:

- dark glass background
- soft sepia/white outline
- no bright white panels
- no raw tables unless styled
- generous breathing room
- strong title
- small metadata line
- concise body
- action buttons as quiet word pills
- close button top-right
- dismiss by click X, Escape, or voice command

Suggested base:

```css
.editorial-surface {
  background: radial-gradient(circle at 18% 12%, rgba(232,228,221,.08), transparent 28%),
              rgba(13,11,10,.94);
  border: 1px solid rgba(232,228,221,.28);
  box-shadow: 0 28px 90px rgba(0,0,0,.55), inset 0 0 0 1px rgba(255,255,255,.035);
  color: #E8E4DD;
  border-radius: 22px;
  backdrop-filter: blur(20px);
}
```

## Surface State

Each visible editorial object should map to a surface record:

```js
{
  id: 'surface_...',
  type: 'summary',
  title: 'Title',
  sourceNodeId: 12,
  sourcePath: 'Folder/Note.md',
  content: 'raw or generated content',
  summary: 'optional summary',
  preview: 'short preview',
  media: [],
  createdAt: 1777279671667
}
```

The UI should maintain:

```js
surfaceRegistry = {
  current: null,
  pinned: [],
  history: []
}
```

## Summary Card Behaviour

When a local LLM summary is ready, it should appear as an editorial surface, not just text in the right panel.

It should include:

- title
- source note/path
- model used
- summary body
- actions: Read, Speak, Deck, Document, Pin
- close X top-right

Dismiss commands:

- close
- close this
- please close this
- dismiss
- hide this
- go back

## Document Surface

The Document action opens the full Obsidian document as a clean one-page editorial reader.

It should include:

- clean title
- small source/path metadata
- Open in Obsidian link
- readable markdown rendering
- media placeholders or resolved media when available
- actions: Pin, Summarize, Deck, Read

## Marp Relationship

Marp decks are the presentation form of editorial content.

A summary, document, comparison, or pinned collection may become:

- a one-card answer
- a dashboard tile
- a Marp outline
- a full Marp deck

The Marp deck should use the same dark editorial style:

- dark background
- sepia/white border
- white/sepia text
- no white grid failure

Marp is output, not the core abstraction. The core abstraction is the surface.

## Visual Desk Relationship

Every editorial surface can be pinned.

When Sam says “pin that”:

- current surface is stored in `surfaceRegistry.pinned`
- a small floating card appears in the Visual Desk tray
- the helper can later summarize, compare, or deck all pinned surfaces

Pinned surfaces are how Sam manages visual work-in-progress.

## Command Routing

Voice and typed commands should use the same router.

Examples:

- “summarise this” → summary surface
- “read this” → Scarlett reads document
- “speak summary” → Scarlett reads summary card
- “marp this” / “deck this” → deck surface
- “pin that” → pin current surface
- “show pinned” → open Visual Desk board
- “summarize pinned” → summary surface across pinned surfaces
- “compare these” → comparison surface
- “show figures” → data surface
- “close” → dismiss current editorial surface
- “show me research” → search visual / result panel

## Command Vocabulary — First Set

Keep the first voice command set small and dependable:

- find
- search
- open
- summarise / summarize / summary
- read
- stop
- repeat
- close / dismiss / hide / go back
- marp / deck / slide
- pin that
- show pinned
- summarize pinned
- compare these

Everything routes through the same command router as typed text.

## Data Exploration Outputs

Data exploration should produce surfaces:

- number cards
- count cards
- figure cards
- comparison cards
- dashboard boards
- Marp decks

The helper should first reason over the visible/pinned context before scanning the whole vault.

## Pre-recorded Scarlett Lines

Pre-recorded Scarlett lines are the right direction for common acknowledgements.

They should be triggered instantly instead of generating TTS every time.

Initial line bank:

- “Got it.”
- “Here’s what I found.”
- “Opening it now.”
- “Summarising this.”
- “Reading it now.”
- “Pinned.”
- “Showing pinned.”
- “I can compare those.”
- “I’ll stop.”
- “Closing this.”
- “No useful content here yet.”
- “Show me what you want to look at next.”

Implementation idea:

```text
mind-vault/audio/scarlett/
  got-it.wav
  found.wav
  opening.wav
  summarising.wav
  reading.wav
  pinned.wav
  showing-pinned.wav
  compare-ready.wav
  stopping.wav
  closing.wav
  no-content.wav
```

Generated Scarlett TTS is reserved for longer summaries and document reading.

## Product Principle

Chat is not the product.

The product is a visual knowledge instrument that turns data into designed, reusable surfaces.
