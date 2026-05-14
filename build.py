"""Render the SEA Batch 1 VO scripts as a /report-style HTML page.

v2: 3 writing-style variants per video, per-variant checkbox + ratings + comment,
sticky bottom prompt-builder panel.
"""
import json, html, os, glob

VARIANTS_DIR = '/Users/steven/Documents/Claude/sea-vo-scripts/variants'
PICKS_FILE = '/Users/steven/Documents/Claude/sea-production/picks/picks_v3_enriched.json'
OUT = '/Users/steven/Documents/Claude/sea-vo-scripts/index.html'


def esc(s):
    return html.escape(str(s or ''))


def card_anchor(cid):
    return cid.lower()


def _overall(s, a, p):
    return round((s + a + p) / 3, 1)


# Load picks (for card meta — title, pillar, format, topic, findings)
picks = []
if os.path.exists(PICKS_FILE):
    picks = json.load(open(PICKS_FILE))
picks_by_id = {p['card_id']: p for p in picks}

# Load variants
all_cards = {}  # card_id -> {id, title, pillar, format_spec, topic, findings, videos: [...]}

for path in sorted(glob.glob(os.path.join(VARIANTS_DIR, 'batch_*.json'))):
    try:
        data = json.load(open(path))
    except Exception:
        continue
    for card in data:
        cid = card['card_id']
        if cid not in all_cards:
            # Pull meta from picks
            p = picks_by_id.get(cid, {})
            all_cards[cid] = {
                'id': cid,
                'title': card.get('card_title') or p.get('card_title', ''),
                'pillar': p.get('pillar', ''),
                'format_spec': p.get('format_spec', ''),
                'topic': p.get('topic', ''),
                'findings': p.get('findings', []),
                'videos': [],
            }
        all_cards[cid]['videos'].extend(card.get('videos', []))


# Preserve ordering by picks file
ordered_cards = []
for p in picks:
    if p['card_id'] in all_cards:
        ordered_cards.append(all_cards[p['card_id']])
# Add any cards not in picks order (defensive)
for cid, c in all_cards.items():
    if c not in ordered_cards:
        ordered_cards.append(c)


def render_variant(card_id, vid_idx, var_idx, variant):
    var_id = f"{card_id}-v{vid_idx+1}-{['a','b','c'][var_idx]}"
    overall = _overall(variant.get('rating_social', 0), variant.get('rating_audience', 0), variant.get('rating_sales', 0))
    style_letter = ['A', 'B', 'C'][var_idx]
    style_label = variant.get('style', '')
    wf_product = variant.get('wf_product', '')
    return f'''
<div class="variant" data-variant-id="{esc(var_id)}">
  <header class="variant-head">
    <label class="variant-check">
      <input type="checkbox" class="vp" data-vid="{esc(var_id)}" data-card="{esc(card_id)}" data-vidx="{vid_idx+1}" data-style="{esc(style_label)}">
      <span class="checkmark"></span>
    </label>
    <div class="variant-title">
      <span class="variant-letter">Variant {style_letter}</span>
      <span class="variant-style">{esc(style_label)}</span>
    </div>
    <div class="variant-ratings">
      <span class="rp social"><span class="rl">Soc</span><span class="rv">{variant.get('rating_social', '-')}</span></span>
      <span class="rp audience"><span class="rl">Aud</span><span class="rv">{variant.get('rating_audience', '-')}</span></span>
      <span class="rp sales"><span class="rl">Sales</span><span class="rv">{variant.get('rating_sales', '-')}</span></span>
      <span class="overall"><span class="rl">Overall</span><span class="rv">{overall}</span></span>
    </div>
  </header>
  <div class="vo-block">
    <p class="vo">{esc(variant.get('vo', ''))}</p>
    <div class="vo-actions">
      <span class="wf-product">↳ {esc(wf_product)}</span>
      <button class="copy-btn" data-vo="{esc(variant.get('vo', ''))}" type="button">Copy VO</button>
    </div>
    <textarea class="variant-comment" data-vid="{esc(var_id)}" placeholder="Comment on this variant. Want different angle? Stronger CTA? Specific tweak? Type it here. Auto-included in the bottom prompt."></textarea>
  </div>
</div>'''


def render_video(card_id, vid_idx, video):
    variants_html = '\n'.join(
        render_variant(card_id, vid_idx, vi, v)
        for vi, v in enumerate(video.get('variants', []))
    )
    return f'''
<article class="video">
  <header class="video-head">
    <span class="video-num">Video {vid_idx+1}</span>
    <h3 class="vt">{esc(video.get('video_title', ''))}</h3>
    <span class="approach">{esc(video.get('approach', ''))}</span>
  </header>
  <div class="variants">
    {variants_html}
  </div>
</article>'''


def render_card(card):
    findings_html = ''
    if card['findings']:
        items = '\n'.join(f'<li>{esc(f)}</li>' for f in card['findings'])
        findings_html = f'''
<details class="findings">
  <summary>Research findings ({len(card['findings'])})</summary>
  <ul>{items}</ul>
</details>'''

    videos_html = '\n'.join(render_video(card['id'], i, v) for i, v in enumerate(card['videos']))

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
  <div class="videos">
    {videos_html}
  </div>
</section>'''


def render_nav(cards):
    items = []
    for c in cards:
        n_variants = sum(len(v.get('variants', [])) for v in c['videos'])
        items.append(
            f'<a href="#{card_anchor(c["id"])}"><span class="nav-id">{esc(c["id"])}</span>'
            f'<span class="nav-t">{esc(c["title"])}</span>'
            f'<span class="nav-n">{n_variants}</span></a>'
        )
    return '\n'.join(items)


total_videos = sum(len(c['videos']) for c in ordered_cards)
total_variants = sum(len(v.get('variants', [])) for c in ordered_cards for v in c['videos'])
total_words = 0
for c in ordered_cards:
    for v in c['videos']:
        for var in v.get('variants', []):
            total_words += len(var.get('vo', '').split())

if total_variants == 0:
    # Show placeholder if no variants yet
    pending_msg = '<div class="pending"><strong>Awaiting redraft</strong><p>3 background agents are producing 3 writing-style variants per picked video. Page will populate when each batch lands.</p></div>'
else:
    pending_msg = ''


HTML_PAGE = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow">
<title>SEA Batch 1 — VO Scripts v2</title>
<style>
:root {{
  --bg: #ffffff;
  --ink: #1d1d1f;
  --ink-soft: #424245;
  --ink-mute: #6e6e73;
  --line: #d2d2d7;
  --line-soft: #e8e8ed;
  --tint: #f5f5f7;
  --pick: #0a6d2f;
  --social: #1a6dcc;
  --audience: #946100;
  --product: #b03060;
  --mono: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: var(--bg); color: var(--ink);
  font-family: -apple-system, "SF Pro Text", "Helvetica Neue", sans-serif;
  font-size: 16px; line-height: 1.55; -webkit-font-smoothing: antialiased; }}

.layout {{ display: grid; grid-template-columns: 260px 1fr; max-width: 1280px;
  margin: 0 auto; gap: 0; }}

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
.nav-id {{ font-family: var(--mono); font-size: 10px;
  color: var(--ink-mute); letter-spacing: 0.04em; }}
.nav-t {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.nav-n {{ font-family: var(--mono); font-size: 10px; color: var(--ink-mute);
  text-align: right; }}

main {{ padding: 60px 56px 200px; min-width: 0; }}

.hero {{ padding-bottom: 36px; border-bottom: 1px solid var(--line);
  margin-bottom: 42px; }}
.kicker {{ font-family: var(--mono); font-size: 11px; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--ink-mute); margin-bottom: 14px; }}
h1 {{ font-size: 32px; line-height: 1.15; letter-spacing: -0.02em;
  font-weight: 600; margin-bottom: 16px; }}
.lede {{ font-size: 17px; color: var(--ink-soft); max-width: 640px;
  line-height: 1.55; }}

.stats {{ display: grid; grid-template-columns: repeat(4, 1fr);
  border: 1px solid var(--line); border-radius: 4px; margin-top: 36px;
  overflow: hidden; }}
.stat {{ padding: 18px 16px; border-right: 1px solid var(--line-soft); }}
.stat:last-child {{ border-right: none; }}
.stat-n {{ font-size: 24px; font-weight: 600; letter-spacing: -0.02em; color: var(--ink); line-height: 1.1; }}
.stat-l {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.1em;
  text-transform: uppercase; color: var(--ink-mute); margin-top: 4px; }}

.pending {{ padding: 22px 26px; border: 1px solid var(--line); border-radius: 6px;
  background: var(--tint); margin: 30px 0; }}
.pending strong {{ display: block; font-size: 14px; margin-bottom: 6px; }}
.pending p {{ font-size: 13px; color: var(--ink-soft); }}

.card {{ margin-bottom: 56px; padding-top: 12px; }}
.card-head {{ padding-bottom: 18px; border-bottom: 1px solid var(--ink);
  margin-bottom: 22px; }}
.card-id {{ font-family: var(--mono); font-size: 11px; color: var(--ink-mute);
  letter-spacing: 0.06em; margin-bottom: 6px; }}
.card-title {{ font-size: 22px; font-weight: 600; letter-spacing: -0.01em;
  line-height: 1.25; margin-bottom: 8px; }}
.card-meta {{ display: flex; flex-wrap: wrap; gap: 14px 22px;
  font-family: var(--mono); font-size: 11px; color: var(--ink-mute);
  letter-spacing: 0.04em; }}

.findings {{ margin-bottom: 28px; border: 1px solid var(--line); border-radius: 4px; overflow: hidden; }}
.findings summary {{ cursor: pointer; padding: 11px 16px;
  font-family: var(--mono); font-size: 11px; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--ink-mute); user-select: none;
  background: var(--tint); }}
.findings summary:hover {{ color: var(--ink); }}
.findings[open] summary {{ border-bottom: 1px solid var(--line); }}
.findings ul {{ padding: 14px 22px 14px 38px; }}
.findings li {{ font-size: 13px; line-height: 1.55; color: var(--ink-soft); margin-bottom: 6px; }}

.videos {{ display: flex; flex-direction: column; gap: 28px; }}
.video {{ }}
.video-head {{ display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap;
  margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px dashed var(--line-soft); }}
.video-num {{ font-family: var(--mono); font-size: 10px; color: var(--ink-mute);
  letter-spacing: 0.08em; text-transform: uppercase; }}
.vt {{ font-size: 17px; font-weight: 600; letter-spacing: -0.01em;
  line-height: 1.3; color: var(--ink); flex: 1; min-width: 280px; }}
.approach {{ font-family: var(--mono); font-size: 10px; letter-spacing: 0.06em;
  text-transform: uppercase; color: var(--ink-mute); padding: 2px 8px;
  border: 1px solid var(--line); border-radius: 100px; }}

.variants {{ display: flex; flex-direction: column; gap: 16px; }}
.variant {{ border: 1px solid var(--line); border-radius: 8px; overflow: hidden;
  background: var(--bg); transition: border-color 0.15s, background 0.15s; }}
.variant.picked {{ border-color: var(--pick); background: rgba(10,109,47,0.025); }}
.variant-head {{ display: grid; grid-template-columns: 28px 1fr auto; gap: 12px;
  align-items: center; padding: 14px 16px 12px; background: var(--tint);
  border-bottom: 1px solid var(--line-soft); }}
.variant.picked .variant-head {{ background: rgba(10,109,47,0.05); }}
.variant-check {{ position: relative; display: inline-flex; cursor: pointer; }}
.variant-check input {{ position: absolute; opacity: 0; cursor: pointer; }}
.checkmark {{ display: block; width: 22px; height: 22px; border: 2px solid var(--line);
  border-radius: 5px; background: var(--bg); transition: all 0.15s; }}
.variant-check input:checked ~ .checkmark {{ background: var(--pick); border-color: var(--pick); }}
.variant-check input:checked ~ .checkmark::after {{ content: '✓'; display: block;
  color: #fff; font-size: 15px; line-height: 18px; text-align: center; font-weight: 700; }}
.variant-title {{ display: flex; align-items: baseline; gap: 8px; flex-wrap: wrap; }}
.variant-letter {{ font-family: var(--mono); font-size: 11px; font-weight: 700;
  letter-spacing: 0.08em; color: var(--ink); }}
.variant-style {{ font-size: 12px; color: var(--ink-soft); }}

.variant-ratings {{ display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; }}
.rp {{ display: inline-flex; align-items: baseline; gap: 3px; padding: 2px 7px;
  border-radius: 100px; font-family: var(--mono); font-weight: 600; }}
.rp .rl {{ font-size: 9px; letter-spacing: 0.06em; text-transform: uppercase; opacity: 0.85; }}
.rp .rv {{ font-size: 10px; }}
.rp.social {{ background: rgba(26,109,204,0.13); color: var(--social); }}
.rp.audience {{ background: rgba(148,97,0,0.13); color: var(--audience); }}
.rp.sales {{ background: rgba(176,48,96,0.13); color: var(--product); }}
.overall {{ display: inline-flex; align-items: baseline; gap: 4px; padding: 2px 8px;
  border-left: 1px solid var(--line); margin-left: 4px; font-family: var(--mono); }}
.overall .rl {{ font-size: 9px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-mute); }}
.overall .rv {{ font-size: 13px; font-weight: 700; color: var(--ink); }}

.vo-block {{ padding: 18px 20px 16px; }}
.vo {{ font-size: 15.5px; line-height: 1.7; color: var(--ink);
  font-family: ui-serif, "New York", "Iowan Old Style", "Apple Garamond", Georgia, serif;
  letter-spacing: 0.005em; }}
.vo-actions {{ display: flex; justify-content: space-between; align-items: center;
  margin-top: 14px; flex-wrap: wrap; gap: 8px; }}
.wf-product {{ font-family: var(--mono); font-size: 11px; color: var(--pick);
  letter-spacing: 0.04em; }}
.copy-btn {{ padding: 6px 12px; background: var(--bg); border: 1px solid var(--line);
  border-radius: 100px; font-family: var(--mono); font-size: 10px;
  letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-soft);
  cursor: pointer; transition: all 0.15s; }}
.copy-btn:hover {{ border-color: var(--ink); color: var(--ink); }}
.copy-btn.copied {{ background: var(--pick); color: #fff; border-color: var(--pick); }}
.variant-comment {{ width: 100%; min-height: 50px; padding: 9px 12px;
  border: 1px solid var(--line); border-radius: 6px; font-family: inherit;
  font-size: 13px; line-height: 1.5; resize: vertical; margin-top: 12px;
  background: var(--bg); box-sizing: border-box; }}
.variant-comment:focus {{ outline: 1px solid var(--ink); border-color: var(--ink); }}
.variant-comment::placeholder {{ color: rgba(0,0,0,0.32); }}

/* Sticky bottom panel */
.bottom-panel {{ position: fixed; bottom: 0; left: 0; right: 0;
  background: var(--ink); color: #fff; z-index: 100;
  box-shadow: 0 -2px 16px rgba(0,0,0,0.18); }}
.bottom-panel.collapsed .panel-body {{ display: none; }}
.panel-bar {{ display: flex; align-items: center; justify-content: space-between;
  padding: 14px 22px; cursor: pointer; gap: 12px; min-height: 56px; }}
.panel-count {{ font-size: 14px; font-weight: 500; }}
.panel-count .count-zero {{ color: #888; font-weight: 400; }}
.panel-toggle {{ font-family: var(--mono); font-size: 11px; color: #aaa;
  text-transform: uppercase; letter-spacing: 0.05em; }}
.panel-body {{ padding: 6px 22px 18px; max-height: 65vh; overflow-y: auto; }}
.panel-label {{ display: block; font-family: var(--mono); font-size: 10px;
  color: #aaa; text-transform: uppercase; letter-spacing: 0.06em;
  margin: 12px 0 6px; }}
.panel-prompt {{ width: 100%; min-height: 220px; padding: 14px;
  border: 1px solid rgba(255,255,255,0.15); border-radius: 6px;
  background: rgba(255,255,255,0.05); color: #fff; font-family: var(--mono);
  font-size: 12px; line-height: 1.55; resize: vertical; white-space: pre-wrap;
  box-sizing: border-box; }}
.panel-actions {{ display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }}
.panel-btn {{ padding: 11px 18px; border-radius: 8px; font-size: 13px;
  font-weight: 500; cursor: pointer; border: none; min-height: 44px;
  font-family: inherit; }}
.btn-copy {{ background: #fff; color: #111; }}
.btn-copy.copied {{ background: var(--pick); color: #fff; }}

@media (max-width: 920px) {{
  .layout {{ grid-template-columns: 1fr; }}
  aside {{ display: none; }}
  main {{ padding: 32px 18px 200px; }}
  h1 {{ font-size: 24px; }}
  .stats {{ grid-template-columns: repeat(2, 1fr); }}
  .stat {{ border-bottom: 1px solid var(--line-soft); }}
  .card-title {{ font-size: 19px; }}
  .vo {{ font-size: 14.5px; }}
  .variant-head {{ grid-template-columns: 28px 1fr; }}
  .variant-ratings {{ grid-column: 1 / -1; padding-left: 40px; }}
}}
</style>
</head>
<body>
<div class="layout">

<aside>
  <div class="side-kicker">Sparkloop · Step 5 · v2</div>
  <div class="side-title">SEA Batch 1 VO Scripts</div>
  <div class="side-sub">{total_variants} variants · {len(ordered_cards)} cards</div>
  <nav>{render_nav(ordered_cards)}</nav>
</aside>

<main>
  <div class="hero">
    <div class="kicker">Sparkloop · /spark_script v2 · 3 styles per video</div>
    <h1>SEA Brand Channel — Voiceover Scripts</h1>
    <p class="lede">Three writing-style variants per picked video: Story, Tactical, Reframe. Each ends with a sales-driven CTA naming a specific WorldFirst product. Pick the variants you want, drop comments where you want changes. The sticky bottom panel builds the paste-back prompt.</p>
    <div class="stats">
      <div class="stat"><div class="stat-n">{len(ordered_cards)}</div><div class="stat-l">Cards</div></div>
      <div class="stat"><div class="stat-n">{total_videos}</div><div class="stat-l">Videos</div></div>
      <div class="stat"><div class="stat-n">{total_variants}</div><div class="stat-l">Variants</div></div>
      <div class="stat"><div class="stat-n">{total_words:,}</div><div class="stat-l">VO words</div></div>
    </div>
  </div>

  {pending_msg}

  {"".join(render_card(c) for c in ordered_cards)}
</main>

</div>

<!-- Sticky bottom prompt panel -->
<div class="bottom-panel collapsed" id="panel">
  <div class="panel-bar" id="panelBar">
    <div class="panel-count" id="panelCount"><span class="count-zero">0 picked · 0 comments</span></div>
    <div class="panel-toggle" id="panelToggle">expand ↑</div>
  </div>
  <div class="panel-body">
    <span class="panel-label">Paste-back prompt</span>
    <textarea class="panel-prompt" id="panelPrompt" readonly></textarea>
    <div class="panel-actions">
      <button class="panel-btn btn-copy" id="btnCopy">Copy prompt</button>
    </div>
  </div>
</div>

<script>
const STORAGE_KEY = 'sea_vo_variants_v2';

function loadState() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{{"picks":[],"comments":{{}}}}'); }}
  catch (e) {{ return {{picks:[], comments:{{}}}}; }}
}}
function saveState(s) {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(s)); }}

let state = loadState();

// Hydrate checkboxes and comments from state
document.querySelectorAll('.vp').forEach(cb => {{
  const vid = cb.getAttribute('data-vid');
  if (state.picks.includes(vid)) {{
    cb.checked = true;
    cb.closest('.variant').classList.add('picked');
  }}
}});
document.querySelectorAll('.variant-comment').forEach(ta => {{
  const vid = ta.getAttribute('data-vid');
  if (state.comments[vid]) ta.value = state.comments[vid];
}});

function variantInfo(vid) {{
  const cb = document.querySelector(`.vp[data-vid="${{vid}}"]`);
  if (!cb) return null;
  const variant = cb.closest('.variant');
  const card_id = cb.getAttribute('data-card');
  const vidx = cb.getAttribute('data-vidx');
  const style = cb.getAttribute('data-style');
  const video_title = variant.closest('.video').querySelector('.vt').textContent;
  const letter = variant.querySelector('.variant-letter').textContent;
  return {{ vid, card_id, vidx, style, video_title, letter }};
}}

function buildPrompt() {{
  const picks = state.picks.map(variantInfo).filter(Boolean);
  const commentEntries = Object.entries(state.comments).filter(([k,v]) => (v||'').trim());

  const lines = [
    '== SEA VO scripts v1 paste-back ==',
    '',
    `PICKED VARIANTS (${{picks.length}}):`,
  ];
  if (picks.length === 0) lines.push('  (none yet)');
  picks.forEach(p => {{
    lines.push(`  ${{p.card_id}} / Video ${{p.vidx}}: "${{p.video_title}}" / ${{p.letter}} ${{p.style}}`);
  }});

  lines.push('');
  lines.push(`COMMENTS (${{commentEntries.length}}):`);
  if (commentEntries.length === 0) lines.push('  (none)');
  commentEntries.forEach(([k, c]) => {{
    const info = variantInfo(k);
    if (info) {{
      lines.push(`  ${{info.card_id}} / Video ${{info.vidx}} / ${{info.letter}}: "${{c.trim()}}"`);
    }}
  }});

  lines.push('');
  lines.push('Action:');
  lines.push('  - No comments → finalize picked variants and deliver');
  lines.push('  - Comments present → produce revised variants on flagged ones based on the comment direction');

  return lines.join('\\n');
}}

function updatePanel() {{
  const pc = state.picks.length;
  const cc = Object.values(state.comments).filter(v => (v||'').trim()).length;
  const ctx = document.getElementById('panelCount');
  if (pc === 0 && cc === 0) {{
    ctx.innerHTML = '<span class="count-zero">0 picked · 0 comments</span>';
  }} else {{
    ctx.textContent = `${{pc}} picked · ${{cc}} comments`;
  }}
  document.getElementById('panelPrompt').value = buildPrompt();
}}

// Checkbox handlers
document.querySelectorAll('.vp').forEach(cb => {{
  cb.addEventListener('change', () => {{
    const vid = cb.getAttribute('data-vid');
    if (cb.checked) {{
      if (!state.picks.includes(vid)) state.picks.push(vid);
      cb.closest('.variant').classList.add('picked');
    }} else {{
      state.picks = state.picks.filter(v => v !== vid);
      cb.closest('.variant').classList.remove('picked');
    }}
    saveState(state);
    updatePanel();
  }});
}});

// Comment handlers
document.querySelectorAll('.variant-comment').forEach(ta => {{
  ta.addEventListener('input', () => {{
    const vid = ta.getAttribute('data-vid');
    if (ta.value.trim()) state.comments[vid] = ta.value;
    else delete state.comments[vid];
    saveState(state);
    updatePanel();
  }});
}});

// Copy individual VO
document.querySelectorAll('.copy-btn').forEach(btn => {{
  btn.addEventListener('click', async (e) => {{
    e.stopPropagation();
    const vo = btn.getAttribute('data-vo');
    try {{
      await navigator.clipboard.writeText(vo);
      btn.textContent = 'Copied';
      btn.classList.add('copied');
      setTimeout(() => {{ btn.textContent = 'Copy VO'; btn.classList.remove('copied'); }}, 1500);
    }} catch (e) {{ console.error(e); }}
  }});
}});

// Panel expand/collapse
const panel = document.getElementById('panel');
document.getElementById('panelBar').addEventListener('click', () => {{
  panel.classList.toggle('collapsed');
  document.getElementById('panelToggle').textContent = panel.classList.contains('collapsed') ? 'expand ↑' : 'collapse ↓';
}});

// Copy prompt
document.getElementById('btnCopy').addEventListener('click', async () => {{
  const text = document.getElementById('panelPrompt').value;
  try {{
    await navigator.clipboard.writeText(text);
    const btn = document.getElementById('btnCopy');
    btn.textContent = 'Copied';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copy prompt'; btn.classList.remove('copied'); }}, 1500);
  }} catch (e) {{ console.error(e); }}
}});

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

updatePanel();
</script>
</body>
</html>
'''

with open(OUT, 'w') as f:
    f.write(HTML_PAGE)

print(f"Built: {OUT}")
print(f"Cards: {len(ordered_cards)} · Videos: {total_videos} · Variants: {total_variants} · Words: {total_words:,}")
