# Next Implementation Pass

## Goal

Rebuild Mind Vault around the actual secret sauce: the LLM wiki graph.

The app should be fast because it uses structure first, not because an LLM reads everything.

## Pass 1 — Index-First Graph Loading

- Load `data/vault-index.json` in `Mind_Vault.html`.
- Draw every note shell from the index.
- Draw real `[[wikilink]]` edges from the index.
- Keep note bodies lazy-loaded.
- Show link/backlink counts immediately.
- Stop hiding most nodes for large vaults.

## Pass 2 — Reliable Panel

Panel must always show useful information:

- title
- path
- category
- tags
- outgoing links
- backlinks
- degree
- modified time
- connected notes
- buttons: Pin, Marp, Page, Read, Load Content

Content preview appears only if body is available.

## Pass 3 — Local Search / Command Line

- Restore local search/input.
- Search index titles, paths, tags, links, backlinks.
- Show matching nodes visually.
- Do not require voice.
- Do not require Gemini.

## Pass 4 — Local Listener Mode

- `Mind` activates microphone only.
- Speech-to-text routes command to local graph operations.
- No generated voice reply by default.
- Visual output is the answer.

## Pass 5 — Presentation Surface

- Repair/enhance inline Marp deck overlay.
- Add generated info-page surface.
- Add discard/close command.
- Prepare for document stack carousel.

## Pass 6 — Daily Index Confidence

- Verify LaunchAgent daily index generation.
- Add visible index timestamp/stats in UI.
- Add manual rebuild button later.

## Explicit Non-Goals For Now

- Gemini Live integration
- full-vault context injection
- live conversational assistant reply loop
- generated local voice except document reading

## Research Task

Research best ways to present information beautifully online:

- animated lists
- stats panels
- charts
- comparisons
- slide/deck surfaces
- PDF-style generated reports
- 3D document stacks

This will shape Mind Vault's stage layer.
