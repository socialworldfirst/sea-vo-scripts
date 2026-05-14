"""Render the SEA Batch 1 VO scripts as a /report-style HTML page."""
import json, html, os

DATA = json.load(open('/tmp/sea_vo_data.json'))
OUT = '/Users/steven/Documents/Claude/sea-vo-scripts/index.html'


def esc(s):
    return html.escape(s or '')


def card_anchor(cid):
    return cid.lower().replace('-', '-')


def render_card(card):
    findings_html = ''
    if card['findings']:
        items = '\n'.join(f'<li>{esc(f)}</li>' for f in card['findings'])
        findings_html = f'''
<details class="findings">
  <summary>Research findings ({len(card['findings'])})</summary>
  <ul>{items}</ul>
</details>'''

    scripts_html = []
    for i, s in enumerate(card['scripts'], 1):
        wc = s['word_count']
        secs = round(wc / 2.5)  # 150 wpm ≈ 2.5 wps
        scripts_html.append(f'''
<article class="script" data-script-id="{card_anchor(card['id'])}-s{i}">
  <header class="script-head">
    <div class="script-meta">
      <span class="approach">{esc(s['approach'])}</span>
      <span class="duration">{wc} words · ~{secs}s</span>
    </div>
    <h3 class="vt">{esc(s['video_title'])}</h3>
  </header>
  <div class="vo-block">
    <p class="vo">{esc(s['vo'])}</p>
    <button class="copy-btn" data-vo="{esc(s['vo'])}" type="button">Copy VO</button>
  </div>
</article>''')

    return f'''
<section class="card" id="{card_anchor(card['id'])}">
  <header class="card-head">
    <div class="card-id">{esc(card['id'])}</div>
    <h2 class="card-title">{esc(card['title'])}</h2>
    <div class="card-meta">
      <span>Pillar {esc(card['pillar'])}</span>
      <span>{esc(card['format_spec'])}</span>
      <span>Topic {esc(card['topic'])}</span>
    </div>
  </header>
  {findings_html}
  <div class="scripts">
    {"".join(scripts_html)}
  </div>
</section>'''


def render_nav(cards):
    items = []
    for c in cards:
        items.append(
            f'<a href="#{card_anchor(c["id"])}"><span class="nav-id">{esc(c["id"])}</span>'
            f'<span class="nav-t">{esc(c["title"])}</span>'
            f'<span class="nav-n">{len(c["scripts"])}</span></a>'
        )
    return '\n'.join(items)


total_scripts = sum(len(c['scripts']) for c in DATA)
total_words = sum(s['word_count'] for c in DATA for s in c['scripts'])
total_seconds = round(total_words / 2.5)
total_minutes = round(total_seconds / 60)


HTML_PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>SEA Batch 1 — Voiceover Scripts</title>
<style>
:root {{
  --bg: #ffffff;
  --ink: #1d1d1f;
  --ink-soft: #424245;
  --ink-mute: #6e6e73;
  --line: #d2d2d7;
  --line-soft: #e8e8ed;
  --tint: #f5f5f7;
  --accent: #1d1d1f;
  --pick: #0a6d2f;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: var(--bg); color: var(--ink);
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
  font-size: 16px; line-height: 1.55; -webkit-font-smoothing: antialiased; }}

.layout {{ display: grid; grid-template-columns: 260px 1fr; max-width: 1200px;
  margin: 0 auto; gap: 0; }}

/* Sidebar */
aside {{ position: sticky; top: 0; height: 100vh; overflow-y: auto;
  padding: 40px 22px 40px 28px; border-right: 1px solid var(--line);
  background: var(--bg); }}
aside .side-kicker {{ font-family: var(--mono); font-size: 10px;
  letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-mute);
  margin-bottom: 14px; }}
aside .side-title {{ font-size: 15px; font-weight: 600; margin-bottom: 4px;
  letter-spacing: -0.01em; line-height: 1.25; }}
aside .side-sub {{ font-size: 11px; color: var(--ink-mute); margin-bottom: 24px;
  font-family: var(--mono); letter-spacing: 0.04em; }}
nav {{ display: flex; flex-direction: column; gap: 2px; }}
nav a {{ display: grid; grid-template-columns: 54px 1fr 20px; gap: 8px;
  align-items: baseline; padding: 7px 0;
  text-decoration: none; color: var(--ink-soft);
  border-bottom: 1px solid var(--line-soft); font-size: 12px; line-height: 1.35; }}
nav a:hover {{ color: var(--ink); }}
nav a.active {{ color: var(--ink); font-weight: 600; }}
nav a.active .nav-id {{ color: var(--ink); }}
.nav-id {{ font-family: var(--mono); font-size: 10px;
  color: var(--ink-mute); letter-spacing: 0.04em; }}
.nav-t {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.nav-n {{ font-family: var(--mono); font-size: 10px; color: var(--ink-mute);
  text-align: right; }}

main {{ padding: 60px 60px 120px; min-width: 0; }}

.hero {{ padding-bottom: 36px; border-bottom: 1px solid var(--line);
  margin-bottom: 42px; }}
.kicker {{ font-family: var(--mono); font-size: 11px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-mute); margin-bottom: 14px; }}
h1 {{ font-size: 36px; line-height: 1.15; letter-spacing: -0.02em;
  font-weight: 600; margin-bottom: 16px; }}
.lede {{ font-size: 17px; color: var(--ink-soft); max-width: 640px;
  line-height: 1.55; }}

.stats {{ display: grid; grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--line); border-radius: 4px; margin-top: 36px;
  overflow: hidden; }}
.stat {{ padding: 18px 16px; border-right: 1px solid var(--line-soft); }}
.stat:last-child {{ border-right: none; }}
.stat-n {{ font-size: 26px; font-weight: 600; letter-spacing: -0.02em; color: var(--ink); line-height: 1.1; }}
.stat-l {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-mute); margin-top: 4px; }}

.card {{ margin-bottom: 56px; padding-top: 12px; }}
.card-head {{ padding-bottom: 18px; border-bottom: 1px solid var(--ink);
  margin-bottom: 22px; }}
.card-id {{ font-family: var(--mono); font-size: 11px; color: var(--ink-mute);
  letter-spacing: 0.06em; margin-bottom: 6px; }}
.card-title {{ font-size: 24px; font-weight: 600; letter-spacing: -0.01em;
  line-height: 1.25; margin-bottom: 8px; }}
.card-meta {{ display: flex; flex-wrap: wrap; gap: 14px 22px;
  font-family: var(--mono); font-size: 11px; color: var(--ink-mute);
  letter-spacing: 0.04em; }}

.findings {{ margin-bottom: 28px; border: 1px solid var(--line); border-radius: 4px;
  padding: 0; overflow: hidden; }}
.findings summary {{ cursor: pointer; padding: 12px 16px;
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--ink-mute); user-select: none;
  background: var(--tint); }}
.findings summary:hover {{ color: var(--ink); }}
.findings[open] summary {{ border-bottom: 1px solid var(--line); }}
.findings ul {{ padding: 14px 22px 14px 38px; }}
.findings li {{ font-size: 13px; line-height: 1.55; color: var(--ink-soft);
  margin-bottom: 6px; }}
.findings li:last-child {{ margin-bottom: 0; }}

.scripts {{ display: flex; flex-direction: column; gap: 24px; }}
.script {{ border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }}
.script-head {{ padding: 16px 22px 14px; border-bottom: 1px solid var(--line-soft);
  background: var(--tint); }}
.script-meta {{ display: flex; justify-content: space-between;
  align-items: baseline; margin-bottom: 6px; }}
.approach {{ font-family: var(--mono); font-size: 10px;
  letter-spacing: 0.1em; text-transform: uppercase;
  color: var(--ink-soft); font-weight: 600; }}
.duration {{ font-family: var(--mono); font-size: 10px;
  letter-spacing: 0.06em; color: var(--ink-mute); }}
.vt {{ font-size: 17px; font-weight: 600; letter-spacing: -0.01em;
  line-height: 1.3; color: var(--ink); }}
.vo-block {{ padding: 22px 24px 16px; position: relative; }}
.vo {{ font-size: 16px; line-height: 1.7; color: var(--ink);
  font-family: ui-serif, "New York", "Iowan Old Style", "Apple Garamond", Georgia, serif;
  letter-spacing: 0.005em; }}
.copy-btn {{ margin-top: 14px; padding: 7px 14px; background: var(--bg);
  border: 1px solid var(--line); border-radius: 100px;
  font-family: var(--mono); font-size: 10px; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--ink-soft); cursor: pointer;
  transition: all 0.15s; }}
.copy-btn:hover {{ border-color: var(--ink); color: var(--ink); }}
.copy-btn.copied {{ background: var(--pick); color: #fff; border-color: var(--pick); }}

.foot {{ margin-top: 60px; padding-top: 22px; border-top: 1px solid var(--line);
  font-family: var(--mono); font-size: 10px; color: var(--ink-mute);
  letter-spacing: 0.06em; text-transform: uppercase; }}
.foot a {{ color: var(--ink); text-decoration: none; border-bottom: 1px solid var(--line); padding-bottom: 1px; }}

@media (max-width: 920px) {{
  .layout {{ grid-template-columns: 1fr; }}
  aside {{ display: none; }}
  main {{ padding: 36px 22px 100px; }}
  h1 {{ font-size: 26px; }}
  .stats {{ grid-template-columns: repeat(2, 1fr); }}
  .stat {{ border-bottom: 1px solid var(--line-soft); }}
  .card-title {{ font-size: 20px; }}
  .vo-block {{ padding: 18px 18px 14px; }}
  .vo {{ font-size: 15px; }}
}}
</style>
</head>
<body>
<div class="layout">

<aside>
  <div class="side-kicker">Sparkloop · Step 5</div>
  <div class="side-title">SEA Batch 1 Voiceover Scripts</div>
  <div class="side-sub">{total_scripts} scripts · {len(DATA)} cards</div>
  <nav>{render_nav(DATA)}</nav>
</aside>

<main>
  <div class="hero">
    <div class="kicker">Sparkloop · /spark_script output · {esc("Pure VO format")}</div>
    <h1>SEA Brand Channel Batch 1 — Voiceover Scripts</h1>
    <p class="lede">Pure reading copy for talent. Each block is one short-form reel, start to finish, no timing markers or shot direction. Director and editor handle visuals separately at shoot time. Default talent lead: Heng Hui Mei.</p>
    <div class="stats">
      <div class="stat"><div class="stat-n">{len(DATA)}</div><div class="stat-l">Cards</div></div>
      <div class="stat"><div class="stat-n">{total_scripts}</div><div class="stat-l">Scripts</div></div>
      <div class="stat"><div class="stat-n">{total_words:,}</div><div class="stat-l">VO words</div></div>
      <div class="stat"><div class="stat-n">~{total_minutes}m</div><div class="stat-l">Total speak time</div></div>
    </div>
  </div>

  {"".join(render_card(c) for c in DATA)}

  <div class="foot">
    Production cards · <a href="https://socialworldfirst.github.io/sea-production/">sea-production</a> ·
    Content bank · <a href="https://socialworldfirst.github.io/sea-content-bank/">sea-content-bank</a>
  </div>
</main>

</div>

<script>
// Scrollspy
const nav_links = document.querySelectorAll('nav a');
const cards = document.querySelectorAll('.card');
const observer = new IntersectionObserver(entries => {{
  entries.forEach(e => {{
    if (e.isIntersecting) {{
      const id = e.target.id;
      nav_links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + id));
    }}
  }});
}}, {{ rootMargin: '-30% 0px -60% 0px' }});
cards.forEach(c => observer.observe(c));

// Copy buttons
document.querySelectorAll('.copy-btn').forEach(btn => {{
  btn.addEventListener('click', async () => {{
    const vo = btn.getAttribute('data-vo');
    try {{
      await navigator.clipboard.writeText(vo);
      const orig = btn.textContent;
      btn.textContent = 'Copied';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('copied'); }}, 1500);
    }} catch (e) {{
      console.error(e);
    }}
  }});
}});
</script>
</body>
</html>
'''

with open(OUT, 'w') as f:
    f.write(HTML_PAGE)

print(f"Built: {OUT}")
print(f"Cards: {len(DATA)} · Scripts: {total_scripts} · Words: {total_words:,}")
