#!/usr/bin/env python3
"""Mind Vault Server — static files + Marp slide generation.

Serves:
  /           → Mind_Vault.html
  /data/*     → vault-index.json etc.
  /marp       → POST endpoint: converts markdown to slide deck HTML
  /*          → static files from SERVE_DIR

No Gemini dependency. Marp uses the local CLI.
"""

import json
import os
import re
import subprocess
import tempfile
import sys
import time
from pathlib import Path
from aiohttp import web, ClientSession, ClientTimeout

SERVE_DIR = Path(__file__).parent
MARp_CLI = "/opt/homebrew/bin/marp"
PORT = int(os.environ.get("MIND_VAULT_PORT", "8788"))
MC_SERVER = os.environ.get("MC_SERVER", "http://127.0.0.1:8787")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
MIND_VAULT_MODEL = os.environ.get("MIND_VAULT_MODEL", "gemma4:e4b")
SCARLETT_LAB_MODEL = os.environ.get("SCARLETT_LAB_MODEL", "qwen3.6:35b")
RECEPTIONIST_DIR = Path(os.path.expanduser("~/AI/OpenClaw/dev/receptionist"))
if str(RECEPTIONIST_DIR) not in sys.path:
    sys.path.insert(0, str(RECEPTIONIST_DIR))



VAULTS = {
    "mission-control": Path(os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Mission Control")),
    "samg.studio": Path(os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/samg.studio")),
    "ams": Path(os.path.expanduser("~/Library/Mobile Documents/iCloud~md~obsidian/Documents/AMS")),
}
TECH_JUNK = {".obsidian", ".smart-env", ".git", "node_modules", ".mind-vault"}

def _safe_vault(vault_key):
    key = vault_key or "mission-control"
    root = VAULTS.get(key)
    if not root:
        return None, key
    return root, key

def _safe_child(root, rel):
    path = (root / rel).resolve()
    root_resolved = root.resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError:
        return None
    return path

def _local_vault_files(root, key):
    files = []
    if not root.exists():
        return files
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")
        if any(part in TECH_JUNK for part in parts):
            continue
        if key == "mission-control" and parts and parts[0] in {"Alfred", "Archive", "memory"}:
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        files.append({
            "name": path.name,
            "path": rel,
            "size": stat.st_size,
            "modified": int(stat.st_mtime * 1000),
            "vault": key,
        })
    files.sort(key=lambda f: f["path"].lower())
    return files

async def handle_local_vault_tree(request):
    key = request.query.get("vault", "mission-control")
    root, key = _safe_vault(key)
    if not root:
        return web.json_response({"ok": False, "error": "Unknown vault"}, status=404)
    files = _local_vault_files(root, key)
    return web.json_response({"ok": True, "vault": key, "root": str(root), "files": files})

async def handle_local_vault_file(request):
    key = request.query.get("vault", "mission-control")
    rel = request.query.get("path", "")
    root, key = _safe_vault(key)
    if not root:
        return web.json_response({"ok": False, "error": "Unknown vault"}, status=404)
    if not rel:
        return web.json_response({"ok": False, "error": "Missing path parameter"}, status=400)
    path = _safe_child(root, rel)
    if not path or not path.exists() or not path.is_file():
        return web.json_response({"ok": False, "error": "File not found"}, status=404)
    if any(part in TECH_JUNK for part in rel.split("/")):
        return web.json_response({"ok": False, "error": "Ignored file"}, status=403)
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return web.json_response({"ok": True, "vault": key, "path": rel, "content": content})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

# ── Marp slide generation ──────────────────────────────────────────

DECK_STYLE = """
  html, body { background:#0D0B0A !important; color-scheme:dark; }
  section {
    background: radial-gradient(circle at 18% 20%, rgba(232,228,221,.08), transparent 28%),
                radial-gradient(circle at 82% 78%, rgba(154,139,122,.10), transparent 30%),
                #0D0B0A !important;
    color: #E8E4DD !important;
    color-scheme: dark;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif;
    letter-spacing: -0.02em;
    padding-bottom: 96px !important;
    box-sizing: border-box;
    border: 0 !important;
    box-shadow: inset 0 0 0 1px rgba(232,228,221,.08);
  }
  section::after { color: rgba(232,228,221,.48); bottom: 28px; }
  section.lead { text-align: left; justify-content: center; }
  h1 { font-size: 72px; color: #F4EFE7; line-height: .94; }
  h2 { color: #E8E4DD; font-size: 44px; }
  h3 { color: #C9BFAF; }
  p, li { font-size: 28px; line-height: 1.38; color: #E8E4DD; }
  ul { padding-left: 1.1em; }
  strong { color: #FFFFFF; }
  a { color: #E8E4DD; text-decoration-color: rgba(232,228,221,.45); }
  code, pre { background: rgba(255,255,255,.06); color: #F4EFE7; }
  table { border-collapse: collapse; background: rgba(13,11,10,.88) !important; color:#E8E4DD !important; box-shadow:0 0 0 1px rgba(232,228,221,.10); }
  th { background: rgba(232,228,221,.12) !important; color:#F4EFE7 !important; border-color: rgba(232,228,221,.24) !important; }
  td { background: rgba(255,255,255,.035) !important; color:#E8E4DD !important; border-color: rgba(232,228,221,.18) !important; }
  tr:nth-child(even) td { background: rgba(255,255,255,.06) !important; }
  footer { color: rgba(232,228,221,.45); }
"""

MARP_DARK_SHELL_STYLE = """
<style id="mind-vault-marp-dark-shell">
  html, body, .bespoke-marp-parent, #\\:\\$p {
    background:#0D0B0A !important;
    color-scheme:dark !important;
  }
  svg[data-marpit-svg], svg.bespoke-marp-slide, foreignObject {
    background:#0D0B0A !important;
  }
  body[data-bespoke-view="overview"] {
    background:#0D0B0A !important;
  }
  body[data-bespoke-view="overview"] .bespoke-marp-parent {
    background:#0D0B0A !important;
    gap:28px !important;
  }
  body[data-bespoke-view="overview"] .bespoke-marp-parent svg.bespoke-marp-slide {
    --bov-selected:rgba(232,228,221,.35) !important;
    --bov-focus:#1A1714 !important;
    --bov-focus-outline:rgba(232,228,221,.18) !important;
    background:#0D0B0A !important;
    background-image:none !important;
    border-radius:14px !important;
    box-shadow:0 18px 60px rgba(0,0,0,.48), 0 0 0 1px rgba(232,228,221,.10) !important;
  }
  section, section[data-theme="default"] {
    background:radial-gradient(circle at 18% 20%, rgba(232,228,221,.08), transparent 28%),
               radial-gradient(circle at 82% 78%, rgba(154,139,122,.10), transparent 30%),
               #0D0B0A !important;
    color:#E8E4DD !important;
    color-scheme:dark !important;
    padding-bottom:96px !important;
    box-sizing:border-box !important;
  }
  section::after { bottom:28px !important; }
</style>
"""


def _deck_markdown(title, markdown):
    body = re.sub(r"^---[\s\S]*?---", "", markdown or "").strip()
    body = re.sub(r"```[\s\S]*?```", "", body).strip()
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    sections = re.split(r"\n(?=##?\s+)", body)
    slides = [f"<!-- _class: lead -->\n# {title}\n\nA visual reading from Mind Vault", "---"]
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        lines = []
        for line in sec.splitlines():
            if len(lines) > 10:
                break
            if line.strip().startswith('###'):
                line = '##' + line.lstrip('#')
            lines.append(line)
        sec = "\n".join(lines).strip()
        if len(sec) > 1050:
            sec = sec[:1050].rsplit(" ", 1)[0] + "…"
        slides.append(sec)
        slides.append("---")
    return (
        "---\nmarp: true\ntheme: default\npaginate: true\nsize: 16:9\nstyle: |"
        + DECK_STYLE
        + "\n---\n\n"
        + "\n\n".join(slides)
    )


async def handle_marp(request):
    try:
        data = await request.json()
        title = re.sub(r"[^A-Za-z0-9 _.-]", "", data.get("title") or "Mind Vault")[:80]
        markdown = data.get("markdown") or ""
        with tempfile.TemporaryDirectory(prefix="mind-vault-marp-") as tmp:
            md_path = Path(tmp) / "deck.md"
            html_path = Path(tmp) / "deck.html"
            md_path.write_text(_deck_markdown(title, markdown), encoding="utf-8")
            result = subprocess.run(
                [MARp_CLI, str(md_path), "-o", str(html_path), "--html"],
                capture_output=True, text=True, timeout=20,
            )
            if result.returncode != 0:
                return web.Response(text=f"<pre>{result.stderr}</pre>", status=500, content_type="text/html")
            html = html_path.read_text(encoding="utf-8")
            html = html.replace("</head>", f"{MARP_DARK_SHELL_STYLE}</head>", 1)
            return web.Response(text=html, content_type="text/html")
    except Exception as e:
        return web.Response(text=f"<pre>Marp error: {e}</pre>", status=500, content_type="text/html")



def _clean_doc_text(text, max_chars=12000):
    text = re.sub(r"^---[\s\S]*?---", "", text or "").strip()
    text = re.sub(r"```[\s\S]*?```", "", text).strip()
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


def _speech_chunks(text, max_chars=480, max_total=9000):
    text = _clean_doc_text(text, max_total)
    parts = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for part in parts:
        if not part:
            continue
        if len(cur) + len(part) + 1 > max_chars and cur:
            chunks.append(cur.strip())
            cur = part
        else:
            cur = (cur + " " + part).strip()
    if cur:
        chunks.append(cur.strip())
    return chunks[:20]


# ── Scarlett Lab bridge ────────────────────────────────────────────

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "what", "where", "when", "how",
    "why", "are", "you", "your", "about", "into", "from", "dans", "avec", "pour",
    "quoi", "qui", "que", "est", "les", "des", "une", "mon", "mes", "notre",
}


def _query_terms(text):
    words = re.findall(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9'’-]{2,}", (text or "").lower())
    return [w for w in words if w not in STOPWORDS]


def _source_snippet(text, terms, max_chars=620):
    clean = _clean_doc_text(text, max_chars=14000)
    lower = clean.lower()
    hit = min([lower.find(t) for t in terms if lower.find(t) >= 0] or [0])
    start = max(0, hit - 180)
    end = min(len(clean), start + max_chars)
    return clean[start:end].strip()


def _search_lab_vault(vault_key, question, limit=5, current_path=None, current_content=None):
    root, key = _safe_vault(vault_key)
    if not root:
        return [], key
    terms = _query_terms(question)
    scored = []

    if current_path and current_content:
        scored.append({
            "path": current_path,
            "title": Path(current_path).stem,
            "score": 1000,
            "snippet": _source_snippet(current_content, terms),
            "reason": "selected_node",
        })

    for meta in _local_vault_files(root, key):
        rel = meta.get("path") or ""
        if current_path and rel == current_path:
            continue
        path = _safe_child(root, rel)
        if not path:
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        title = Path(rel).stem
        hay = f"{title} {rel} {_clean_doc_text(raw, 9000)}".lower()
        score = 0
        for term in terms:
            if term in title.lower():
                score += 16
            if term in rel.lower():
                score += 8
            score += min(hay.count(term), 8)
        if score <= 0:
            continue
        scored.append({
            "path": rel,
            "title": title,
            "score": score,
            "snippet": _source_snippet(raw, terms),
            "reason": "term_match",
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:limit], key


async def handle_scarlett_lab_ask(request):
    """Internal Mind Vault ⇄ Scarlett Lab bridge.

    Owned by Mind Vault: local vault access + Scarlett-style service phrasing
    without merging the commercial Scarlett customer-instance product into
    Mind Vault.
    """
    start = time.time()
    try:
        data = await request.json()
        question = (data.get("question") or "").strip()
        if not question:
            return web.json_response({"ok": False, "error": "Missing question"}, status=400)
        vault_key = data.get("vault") or "mission-control"
        lang = data.get("language") or ("fr" if vault_key == "ams" else "en")
        current_node = data.get("currentNode") or {}
        current_path = current_node.get("path") or ""
        current_content = current_node.get("content") or ""

        hits, resolved_vault = _search_lab_vault(
            vault_key,
            question,
            limit=int(data.get("maxSources") or 5),
            current_path=current_path,
            current_content=current_content,
        )
        context = "\n\n---\n\n".join(
            f"Source: {h['path']}\nScore: {h['score']}\nExcerpt: {h['snippet']}"
            for h in hits
        )
        lang_instruction = "Réponds uniquement en français québécois naturel." if str(lang).lower().startswith("fr") else "Answer in natural English."
        prompt = f"""Tu es Scarlett Core dans le banc d'essai Mind Vault de Sam.

Rôle: réceptionniste vocale locale pour l'Académie de Massage Scientifique quand le vault AMS est utilisé.
Style: naturel, bref, chaleureux, premium, sans te présenter et sans dire « je suis Scarlett » sauf si on te le demande.
Source de vérité: utilise seulement le contexte local fourni ci-dessous.
Si l'information n'est pas dans le contexte, dis-le simplement et propose la prochaine action utile.
Ne jamais inventer prix, dates, reconnaissance de diplôme, disponibilité ou conseils médicaux/réglementaires.
{lang_instruction}

Question: {question}

Contexte local:
{context or '(aucune note locale correspondante trouvée)'}
"""
        payload = {
            "model": SCARLETT_LAB_MODEL,
            "messages": [
                {"role": "system", "content": "Tu es Scarlett Core, réceptionniste vocale locale FR-CA pour le lab Mind Vault/AMS. Réponds depuis le contexte local seulement. Ne te présente pas. N'invente jamais les détails sensibles."},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.18, "top_p": 0.9, "num_predict": 900},
        }
        async with ClientSession() as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=ClientTimeout(total=90)) as resp:
                raw = await resp.text()
                if resp.status >= 400:
                    return web.json_response({"ok": False, "error": raw}, status=502)
                out = json.loads(raw)
        answer = (out.get("message", {}).get("content") or "").strip()
        latency = int((time.time() - start) * 1000)
        sources = [h["path"] for h in hits]
        return web.json_response({
            "ok": True,
            "answer": answer,
            "sources": sources,
            "top_score": hits[0]["score"] if hits else 0,
            "refused": False,
            "model": SCARLETT_LAB_MODEL,
            "latency_ms": latency,
            "trace": {
                "mode": "scarlett_lab",
                "vault": resolved_vault,
                "searched": "local_vault_files",
                "current_node": current_path or None,
                "source_count": len(sources),
                "context_chars": len(context),
                "latency_ms": latency,
                "model": SCARLETT_LAB_MODEL,
                "sources": hits,
            },
        })
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


async def handle_voice(request):
    """Generate local Scarlett/Mind Vault audio for text."""
    try:
        data = await request.json()
        text = _clean_doc_text(data.get("text") or "", 9000)
        lang = data.get("language") or "en"
        mode = data.get("mode") or "scarlett"
        if not text:
            return web.Response(text="Missing text", status=400)
        from tts import generate_voice, generate_fast_voice, _crossfade_join
        chunks = _speech_chunks(text, max_chars=460 if mode == "scarlett" else 520)
        if not chunks:
            return web.Response(text="No speakable text", status=400)
        paths = []
        for chunk in chunks:
            path = generate_voice(chunk, lang=lang, speed=0.9) if mode == "scarlett" else generate_fast_voice(chunk, lang=lang, speed=0.95)
            if path:
                paths.append(path)
        if not paths:
            return web.Response(text="TTS failed", status=500)
        audio_path = _crossfade_join(paths) if len(paths) > 1 else paths[0]
        return web.Response(body=Path(audio_path).read_bytes(), content_type="audio/wav")
    except Exception as e:
        return web.Response(text=f"Voice error: {e}", status=500)


async def handle_summarize(request):
    """Summarize one selected vault document with the local Ollama model."""
    try:
        data = await request.json()
        title = (data.get("title") or "Selected note")[:160]
        text = _clean_doc_text(data.get("text") or "", 9000)
        lang = data.get("language") or "en"
        if not text:
            return web.json_response({"ok": False, "error": "Missing text"}, status=400)
        if len(text.strip()) < 80:
            return web.json_response({"ok": True, "summary": "Not enough document content to summarise usefully.", "model": MIND_VAULT_MODEL})
        prompt = f"""You are Mind Vault, summarising one local document for Sam.
Language: {lang}
Title: {title}

Return a concise, speaking-friendly summary in this exact shape:
**What it is:** one sentence.
**Key points:** 3-5 short bullets.
**Next:** one practical next action, only if useful.

Rules: no memo format, no To/From, no generic praise, no long preamble.

Document:
{text}
"""
        payload = {"model": MIND_VAULT_MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.15, "top_p": 0.9, "num_predict": 900}}
        async with ClientSession() as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=ClientTimeout(total=90)) as resp:
                raw = await resp.text()
                if resp.status >= 400:
                    return web.json_response({"ok": False, "error": raw}, status=502)
                out = json.loads(raw)
        summary = (out.get("response") or "").strip()
        summary = re.sub(r"\n?\*\*Next:\*\*\s*\(?None needed\)?\.?\s*$", "", summary, flags=re.I).strip()
        summary = re.sub(r"\n?\*\*Next:\*\*\s*$", "", summary, flags=re.I).strip()
        return web.json_response({"ok": True, "summary": summary, "model": MIND_VAULT_MODEL})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)


# ── Static file serving ────────────────────────────────────────────

async def handle_index(request):
    html = (SERVE_DIR / "Mind_Vault.html").read_bytes()
    return web.Response(body=html, content_type="text/html")


async def handle_static(request):
    rel = request.path.lstrip("/")
    # Compatibility aliases for old public links and previous /vault prefix.
    if not rel or rel in {"vault", "vault/", "live_voice_ui.html"}:
        rel = "Mind_Vault.html"
    elif rel.startswith("vault/"):
        rel = rel[len("vault/"):]
    file_path = SERVE_DIR / rel
    if not file_path.exists() or file_path.is_dir():
        raise web.HTTPNotFound()
    # Security: ensure we don't serve files outside SERVE_DIR
    try:
        file_path.resolve().relative_to(SERVE_DIR.resolve())
    except ValueError:
        raise web.HTTPNotFound()
    content_type = "text/html" if file_path.suffix == ".html" else "application/octet-stream"
    if file_path.suffix == ".json":
        content_type = "application/json"
    elif file_path.suffix == ".js":
        content_type = "application/javascript"
    elif file_path.suffix == ".css":
        content_type = "text/css"
    return web.Response(body=file_path.read_bytes(), content_type=content_type)


async def handle_health(request):
    return web.Response(text="ok")


async def handle_vault_file(request):
    """Proxy vault file content requests to Mission Control API."""
    path = request.query.get("path", "")
    if not path:
        return web.Response(text="Missing path parameter", status=400)
    try:
        async with ClientSession() as session:
            async with session.get(
                f"{MC_SERVER}/api/vault/file",
                params={"path": path},
                timeout=ClientTimeout(total=10)
            ) as resp:
                data = await resp.read()
                return web.Response(body=data, content_type="application/json")
    except Exception as e:
        return web.Response(text=json.dumps({"ok": False, "error": str(e)}), content_type="application/json", status=502)


async def handle_vault_tree(request):
    """Proxy vault tree requests to Mission Control API."""
    try:
        async with ClientSession() as session:
            async with session.get(
                f"{MC_SERVER}/api/vault/tree",
                timeout=ClientTimeout(total=10)
            ) as resp:
                data = await resp.read()
                return web.Response(body=data, content_type="application/json")
    except Exception as e:
        return web.Response(text=json.dumps({"ok": False, "error": str(e)}), content_type="application/json", status=502)


# ── Main ────────────────────────────────────────────────────────────

async def main():
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/vault/file", handle_vault_file)
    app.router.add_get("/api/vault/tree", handle_vault_tree)
    app.router.add_get("/api/local-vault/tree", handle_local_vault_tree)
    app.router.add_get("/api/local-vault/file", handle_local_vault_file)
    app.router.add_post("/marp", handle_marp)
    app.router.add_post("/api/voice", handle_voice)
    app.router.add_post("/api/summarize", handle_summarize)
    app.router.add_post("/api/scarlett-lab/ask", handle_scarlett_lab_ask)
    app.router.add_get("/data/{filename:.*}", handle_static)
    app.router.add_get("/{filename:.*}", handle_static)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Mind Vault server on http://0.0.0.0:{PORT}", flush=True)
    print(f"Marp endpoint: POST /marp", flush=True)
    print(f"Static files: {SERVE_DIR}", flush=True)
    await asyncio.Event().wait()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())