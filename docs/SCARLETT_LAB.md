# Scarlett Lab in Mind Vault

Scarlett Lab is an internal bridge between Mind Vault and Scarlett Core.

It is a lab harness, not a product merge.

## Boundary

- Mind Vault owns the visual knowledge interface: vault loading, graph, panels, source highlighting, and reasoning/access display.
- Scarlett Core owns the voice/service intelligence direction: tone, cached-first voice architecture, prefillers, service rhythm, and future customer-instance behaviour.
- Scarlett Lab lets Mind Vault use Scarlett-style interaction and voice while keeping the commercial Scarlett receptionist product separate.

## First implementation

Mind Vault exposes:

`POST /api/scarlett-lab/ask`

The endpoint:

- receives a question from the Mind Vault UI
- searches the currently selected local vault from the Mind Vault server
- optionally includes the currently selected node as priority context
- asks the local Ollama model for a concise Scarlett-style answer
- returns answer, source paths, model, latency, score, and a small access/reasoning trace

It does not call or mutate customer instances. It does not hard-code AMS behaviour. It does not expose private chain-of-thought. The trace is operational: what vault was searched, which files were used, model, score, and latency.

## Why this shape

This lets Sam test two systems at once:

- Scarlett voice/service feel
- Mind Vault visual source-grounded trust layer

without confusing repo ownership or product positioning.

## Next layers

1. Add cached prefiller playback before the answer returns.
2. Add a richer trace panel: selected node, search terms, source snippets, model path, confidence.
3. Add optional Scarlett Core endpoint support once the core service layer can accept non-customer Mind Vault context cleanly.
4. Add face/avatar surface later; not part of the first bridge.
