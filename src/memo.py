"""Render docs/recommendation.md to docs/recommendation.html (GitHub Pages) and,
when Microsoft Edge or Chrome is available, docs/recommendation.pdf."""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"

CSS = """
:root { color-scheme: light; --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --accent:#2a78d6; --wash:#e8f1fc; --border:rgba(11,11,11,.10); }
@media (prefers-color-scheme: dark) { :root:where(:not([data-theme="light"])) { color-scheme: dark; --page:#0d0d0d; --surface:#1a1a19;
  --ink:#fff; --ink2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --accent:#3987e5; --wash:#16263a; --border:rgba(255,255,255,.10); } }
* { box-sizing: border-box; }
body { margin:0; background:var(--page); color:var(--ink); font:15.5px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 32px 16px 64px; background: var(--page); }
h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; letter-spacing: -0.01em; }
h1 + p em { color: var(--ink2); font-style: normal; font-size: 14px; }
h2 { font-size: 20px; margin: 36px 0 10px; padding-top: 8px; border-top: 1px solid var(--grid); }
h3 { font-size: 16.5px; margin: 24px 0 6px; }
a { color: var(--accent); }
ol, ul { padding-left: 22px; }
li { margin: 5px 0; }
blockquote { margin: 10px 0; padding: 8px 14px; border-left: 3px solid var(--accent); background: var(--wash); color: var(--ink2); border-radius: 0 8px 8px 0; }
blockquote p { margin: 4px 0; }
table { border-collapse: collapse; width: 100%; font-size: 13.5px; margin: 10px 0 14px; display: block; overflow-x: auto; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--grid); vertical-align: top; }
th { color: var(--ink2); font-weight: 600; }
code { font-size: 13px; background: var(--grid); padding: 1px 5px; border-radius: 4px; }
hr { border: 0; border-top: 1px solid var(--grid); margin: 36px 0; }
h2:first-of-type + ol { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px 18px 14px 36px; }
@media print {
  body { background: #fff; font-size: 11pt; } main { max-width: none; padding: 0; background:#fff; }
  h2 { break-after: avoid; } table, blockquote { break-inside: avoid; } a { color: #0b0b0b; }
  @page { size: A4; margin: 16mm 14mm; }
}
"""


def audit_sentence():
    path = ROOT / "data" / "labels" / "gold_audit.csv"
    if path.exists():
        a = pd.read_csv(path)
        done = a[a["verdict"].fillna("").str.strip() != ""]
        if len(done):
            rnd = done[done["why"] == "random"]
            saf = done[done["why"] == "safety flag"]
            ok = lambda d: int(d["verdict"].str.strip().str.lower().isin(["ok", "y", "yes", "correct"]).sum())
            parts = []
            if len(rnd):
                parts.append(f"A person checked {len(rnd)} randomly chosen labels: {ok(rnd)} were right ({ok(rnd) / len(rnd):.0%})")
            if len(saf):
                parts.append(f"and {ok(saf)} of {len(saf)} safety flags were confirmed")
            return " ".join(parts) + "."
    return "A person is checking a random sample of 50 labels and every safety flag; the result is reported in the README."


LIST_ITEM = re.compile(r"^\s*(\d+\.|[-*])\s")


def pymd_compat(md):
    """GitHub-flavoured nesting (2-3 space indents, lists right after a paragraph)
    -> what Python-Markdown expects (4-space indents, blank line before a list)."""
    out = []
    for line in md.split("\n"):
        m = re.match(r"^( {1,3})(\S.*)$", line)
        if m:
            line = "    " + m.group(2)
        if LIST_ITEM.match(line) and not line.startswith(" ") and out and out[-1].strip() \
                and not LIST_ITEM.match(out[-1]) and not out[-1].startswith(" "):
            out.append("")
        out.append(line)
    return "\n".join(out)


def render(owner=None):
    owner = owner or getattr(config, "GITHUB_OWNER", "OWNER")
    dash = f"https://{owner}.github.io/moveinsync-playstore-ratings/"
    repo = f"https://github.com/{owner}/moveinsync-playstore-ratings"
    md = (DOCS / "recommendation.md").read_text(encoding="utf-8")
    md = md.replace("{{DASHBOARD_URL}}", dash).replace("{{REPO_URL}}", repo).replace("{{AUDIT_SENTENCE}}", audit_sentence())
    body = markdown.markdown(pymd_compat(md), extensions=["tables", "sane_lists"])
    body = body.replace(f"{dash}", f'<a href="{dash}">{dash}</a>').replace(f"{repo})", f'<a href="{repo}">{repo}</a>)')
    body = body.replace("<strong>backlog.csv</strong>", '<strong><a href="backlog.csv">backlog.csv</a></strong>')
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Play Store Ratings Recommendation</title>
<meta name="description" content="What is behind MoveInSync's Play Store ratings and what to fix first — ticket-ready recommendation.">
<style>{CSS}</style></head><body><main>{body}</main></body></html>"""
    out = DOCS / "recommendation.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")
    pdf(out)


def pdf(html_path):
    candidates = [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                  r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                  shutil.which("google-chrome") or "", shutil.which("chromium") or ""]
    browser = next((c for c in candidates if c and Path(c).exists()), None)
    if not browser:
        print("no browser for PDF; skipped")
        return
    import tempfile
    import time
    target = DOCS / "recommendation.pdf"
    if target.exists():
        target.unlink()
    profile = tempfile.mkdtemp(prefix="pdfprofile-")  # separate profile so an open browser doesn't swallow the job
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--user-data-dir={profile}",
                    f"--print-to-pdf={target}", html_path.resolve().as_uri()], check=False, timeout=120)
    for _ in range(40):
        if target.exists() and target.stat().st_size > 0:
            break
        time.sleep(1)
    print(f"wrote {target}" if target.exists() else "PDF render failed")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else None)
