#!/usr/bin/env python3
"""
GitHub Project List — 搜索历史项目汇总 HTML 生成器（精简版）

只保留三大板块：
  1. Stars 排行
  2. 分类占比
  3. 项目详情（按分类分组）

用法:
    python github_list.py [选项]
"""

from __future__ import annotations

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

CACHE_DIR = Path.home() / ".cache" / "github-report-skill"
TRACKING_FILE = CACHE_DIR / "project_index.json"

# ========== 分类配色方案 ==========
CATEGORY_COLORS: dict[str, dict[str, str]] = {
    "default":           {"light": "#ebf4ff", "main": "#2b6cb0", "border": "#3182ce", "dark": "#60a5fa", "dark_light": "#1e3a5f"},
    "ai":                {"light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6", "dark": "#a78bfa", "dark_light": "#2e1065"},
    "machine-learning":  {"light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6", "dark": "#a78bfa", "dark_light": "#2e1065"},
    "deep-learning":     {"light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6", "dark": "#a78bfa", "dark_light": "#2e1065"},
    "llm":               {"light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6", "dark": "#a78bfa", "dark_light": "#2e1065"},
    "前端框架":            {"light": "#dbeafe", "main": "#2563eb", "border": "#3b82f6", "dark": "#60a5fa", "dark_light": "#1e3a5f"},
    "frontend":          {"light": "#dbeafe", "main": "#2563eb", "border": "#3b82f6", "dark": "#60a5fa", "dark_light": "#1e3a5f"},
    "ui":                {"light": "#dbeafe", "main": "#2563eb", "border": "#3b82f6", "dark": "#60a5fa", "dark_light": "#1e3a5f"},
    "javascript":        {"light": "#fef9c3", "main": "#a16207", "border": "#ca8a04", "dark": "#fde047", "dark_light": "#422006"},
    "python":            {"light": "#d1fae5", "main": "#047857", "border": "#059669", "dark": "#34d399", "dark_light": "#022c22"},
    "backend":           {"light": "#dcfce7", "main": "#16a34a", "border": "#22c55e", "dark": "#4ade80", "dark_light": "#052e16"},
    "自动化":             {"light": "#e0f2fe", "main": "#0284c7", "border": "#0ea5e9", "dark": "#38bdf8", "dark_light": "#0c4a6e"},
    "automation":        {"light": "#e0f2fe", "main": "#0284c7", "border": "#0ea5e9", "dark": "#38bdf8", "dark_light": "#0c4a6e"},
    "devops":            {"light": "#e0f2fe", "main": "#0284c7", "border": "#0ea5e9", "dark": "#38bdf8", "dark_light": "#0c4a6e"},
    "data":              {"light": "#fce7f3", "main": "#be185d", "border": "#db2777", "dark": "#f472b6", "dark_light": "#4c0519"},
    "database":          {"light": "#fce7f3", "main": "#be185d", "border": "#db2777", "dark": "#f472b6", "dark_light": "#4c0519"},
    "security":          {"light": "#fee2e2", "main": "#b91c1c", "border": "#dc2626", "dark": "#f87171", "dark_light": "#450a0a"},
    "tools":             {"light": "#f5f5f4", "main": "#57534e", "border": "#78716c", "dark": "#a8a29e", "dark_light": "#1c1917"},
    "cli":               {"light": "#f5f5f4", "main": "#57534e", "border": "#78716c", "dark": "#a8a29e", "dark_light": "#1c1917"},
    "game":              {"light": "#ffedd5", "main": "#c2410c", "border": "#ea580c", "dark": "#fb923c", "dark_light": "#431407"},
    "未分类":             {"light": "#f1f5f9", "main": "#475569", "border": "#64748b", "dark": "#94a3b8", "dark_light": "#1e293b"},
}


def resolve_category_colors(category: str) -> dict[str, str]:
    key = (category or "").strip().lower()
    if key in CATEGORY_COLORS:
        return CATEGORY_COLORS[key]
    for pattern, colors in CATEGORY_COLORS.items():
        if pattern and pattern != "default" and pattern in key:
            return colors
    return CATEGORY_COLORS["default"]


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
:root {{
  --bg: #f0f2f5;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #5a5a7a;
  --text-muted: #8e8ea0;
  --border: #e2e5ec;
  --shadow: 0 2px 12px rgba(0,0,0,0.06);
  --radius: 12px;
  --font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono: "SF Mono", "Fira Code", "Consolas", monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
    --bg: #0b1120;
    --card-bg: #161f35;
    --text: #e2e8f0;
    --text-secondary: #8892b0;
    --text-muted: #5a6580;
    --border: #1e2a45;
    --shadow: 0 2px 12px rgba(0,0,0,0.3);
  }}
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
}}
a {{ color: inherit; text-decoration: none; }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 28px 20px 60px; }}

/* ========== Header ========== */
.header {{
  text-align: center;
  margin-bottom: 36px;
  padding: 40px 28px 32px;
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  position: relative;
  overflow: hidden;
}}
.header::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  background: linear-gradient(90deg, #2b6cb0, #7c3aed, #2563eb, #059669, #0284c7);
}}
.header h1 {{ font-size: 1.75rem; font-weight: 700; margin-bottom: 6px; }}
.header .subtitle {{ color: var(--text-secondary); font-size: 0.95rem; }}
.stats-row {{
  display: flex; justify-content: center; gap: 36px; margin-top: 20px; flex-wrap: wrap;
}}
.stat-item {{ text-align: center; }}
.stat-number {{ font-size: 1.5rem; font-weight: 700; color: #2b6cb0; }}
.stat-label {{ font-size: 0.78rem; color: var(--text-muted); margin-top: 2px; }}
@media (prefers-color-scheme: dark) {{ .stat-number {{ color: #60a5fa; }} }}

/* ========== Section ========== */
.section {{ margin-bottom: 36px; }}
.section-title {{
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}}
.section-title .badge {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--border);
  color: var(--text-secondary);
  font-size: 0.72rem;
  font-weight: 600;
  padding: 1px 9px;
  border-radius: 12px;
  margin-left: 4px;
}}

/* ========== Stars Ranking ========== */
.ranking-table {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: var(--card-bg);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow);
}}
.ranking-table th,
.ranking-table td {{
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}}
.ranking-table th {{
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: var(--bg);
}}
.ranking-table tr:last-child td {{ border-bottom: none; }}
.ranking-table tr:hover td {{ background: var(--bg); }}
.rank-num {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px; height: 28px;
  border-radius: 50%;
  font-size: 0.78rem;
  font-weight: 700;
  background: var(--bg);
  color: var(--text-secondary);
}}
.rank-1 {{ background: #fef3c7; color: #b45309; }}
.rank-2 {{ background: #e5e7eb; color: #4b5563; }}
.rank-3 {{ background: #fed7aa; color: #9a3412; }}
@media (prefers-color-scheme: dark) {{
  .rank-1 {{ background: #451a03; color: #fbbf24; }}
  .rank-2 {{ background: #374151; color: #d1d5db; }}
  .rank-3 {{ background: #431407; color: #fb923c; }}
}}
.rank-name {{ font-weight: 600; font-size: 0.92rem; }}
.rank-name a {{ color: var(--accent, #2b6cb0); }}
.rank-name a:hover {{ text-decoration: underline; }}
.rank-stars {{
  font-weight: 700;
  font-size: 0.9rem;
  font-family: var(--font-mono);
  white-space: nowrap;
}}
.rank-lang {{ font-size: 0.78rem; color: var(--text-muted); font-family: var(--font-mono); }}
.rank-bar {{
  width: 100%;
  height: 6px;
  background: var(--bg);
  border-radius: 3px;
  overflow: hidden;
  min-width: 80px;
}}
.rank-bar-fill {{
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}}

/* ========== Category Distribution ========== */
.distribution {{
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 20px 24px;
  box-shadow: var(--shadow);
}}
.dist-item {{
  display: flex;
  align-items: center;
  gap: 12px;
}}
.dist-color {{
  width: 12px; height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.dist-name {{
  font-size: 0.88rem;
  font-weight: 500;
  min-width: 80px;
}}
.dist-bar {{
  flex: 1;
  height: 20px;
  background: var(--bg);
  border-radius: 10px;
  overflow: hidden;
}}
.dist-bar-fill {{
  height: 100%;
  border-radius: 10px;
  transition: width 0.8s ease;
}}
.dist-count {{
  font-size: 0.85rem;
  font-weight: 600;
  min-width: 50px;
  text-align: right;
  font-family: var(--font-mono);
}}

/* ========== Category Group ========== */
.category-group {{
  margin-bottom: 28px;
}}
.category-group:last-child {{ margin-bottom: 0; }}
.category-head {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  padding: 10px 16px;
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}}
.category-head-dot {{
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}}
.category-head-name {{
  font-size: 1rem;
  font-weight: 700;
}}
.category-head-count {{
  font-size: 0.78rem;
  color: var(--text-muted);
  margin-left: auto;
}}

/* ========== Card Grid ========== */
.card-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 14px;
}}
@media (max-width: 480px) {{
  .card-grid {{ grid-template-columns: 1fr; }}
}}
.project-card {{
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.15s;
}}
.project-card:hover {{
  transform: translateY(-2px);
}}
.card-accent {{
  height: 3px; width: 100%; flex-shrink: 0;
}}
.card-body {{
  padding: 14px 16px 12px;
  display: flex;
  flex-direction: column;
  flex: 1;
}}
.card-top {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}}
.card-name {{
  font-size: 0.95rem;
  font-weight: 600;
  word-break: break-all;
  line-height: 1.35;
}}
.card-name:hover {{ text-decoration: underline; }}
.card-stars {{
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 14px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}}
.card-stars svg {{ width: 12px; height: 12px; flex-shrink: 0; }}
.card-desc {{
  color: var(--text-secondary);
  font-size: 0.82rem;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: 8px;
  flex: 1;
}}
.card-footer {{
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}}
.card-tag {{
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 500;
  line-height: 1.5;
}}
.card-link {{
  margin-left: auto;
  font-size: 0.72rem;
  color: var(--text-muted);
  opacity: 0.7;
}}
.card-link:hover {{ opacity: 1; text-decoration: underline; }}

/* ========== Footer ========== */
.footer {{
  text-align: center;
  margin-top: 48px;
  padding: 20px;
  color: var(--text-muted);
  font-size: 0.78rem;
}}
</style>
</head>
<body>
<div class="container">
  <!-- Header -->
  <header class="header">
    <h1>{title}</h1>
    <p class="subtitle">{count} 个项目，累计 {total_stars} ⭐</p>
    <div class="stats-row">
      <div class="stat-item"><div class="stat-number">{count}</div><div class="stat-label">项目总数</div></div>
      <div class="stat-item"><div class="stat-number">{total_stars}</div><div class="stat-label">总 Stars</div></div>
      <div class="stat-item"><div class="stat-number">{cat_count}</div><div class="stat-label">分类数</div></div>
      <div class="stat-item"><div class="stat-number">{avg_stars}</div><div class="stat-label">平均 Stars</div></div>
    </div>
  </header>

  <!-- 1. Stars 排行 -->
  <div class="section">
    <div class="section-title">⭐ Stars 排行 <span class="badge">{count}</span></div>
    <table class="ranking-table">
      <thead>
        <tr><th>#</th><th>项目</th><th>Stars</th><th>语言</th><th></th></tr>
      </thead>
      <tbody>
{ranking_rows}
      </tbody>
    </table>
  </div>

  <!-- 2. 分类占比 -->
  <div class="section">
    <div class="section-title">📊 分类占比 <span class="badge">{cat_count}</span></div>
    <div class="distribution">
{distribution_rows}
    </div>
  </div>

  <!-- 3. 项目详情（按分类分组） -->
  <div class="section">
    <div class="section-title">📋 项目详情 <span class="badge">{count}</span></div>
{category_groups}
  </div>

  <!-- Footer -->
  <div class="footer">
    <p>生成于 {generated_at} · <a href="https://github.com" target="_blank" rel="noopener" style="color:var(--text-secondary);text-decoration:underline">GitHub</a></p>
  </div>
</div>
</body>
</html>
"""


def load_projects() -> list[dict]:
    if not TRACKING_FILE.exists():
        return []
    try:
        data = json.loads(TRACKING_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("projects", [])
    except Exception:
        return []


def render_html(projects: list[dict], title: str, lang: str) -> str:
    count = len(projects)
    total_stars = sum(p.get("stars", 0) or 0 for p in projects)
    avg_stars = round(total_stars / count) if count > 0 else 0

    # 按 stars 倒序
    sorted_projects = sorted(projects, key=lambda p: -(p.get("stars", 0) or 0))

    # 按分类分组
    cat_groups: dict[str, list[dict]] = {}
    for p in projects:
        cat = p.get("category", "未分类") or "未分类"
        cat_groups.setdefault(cat, []).append(p)
    # 组内按 stars 排序
    for cat in cat_groups:
        cat_groups[cat].sort(key=lambda p: -(p.get("stars", 0) or 0))

    # 分类名排序
    sorted_cats = sorted(cat_groups.keys())
    cat_count = len(sorted_cats)

    # ---- Stars 排行行 ----
    max_stars = max(p.get("stars", 0) or 0 for p in sorted_projects) or 1
    ranking_rows_lines = []
    for idx, p in enumerate(sorted_projects):
        rank = idx + 1
        stars = p.get("stars", 0) or 0
        full_name = p.get("full_name", p.get("name", ""))
        url = p.get("url", f"https://github.com/{full_name}")
        desc = p.get("description", "") or ""
        lang_name = p.get("language", "")
        col = resolve_category_colors(p.get("category", ""))
        pct = stars / max_stars * 100

        rank_cls = f"rank-{rank}" if rank <= 3 else ""
        ranking_rows_lines.append(f"""        <tr>
          <td><span class="rank-num {rank_cls}">{rank}</span></td>
          <td>
            <div class="rank-name"><a href="{url}" style="color:{col['main']}" target="_blank" rel="noopener">{full_name}</a></div>
            <div style="font-size:0.78rem;color:var(--text-muted);margin-top:2px">{desc[:80]}{'...' if len(desc) > 80 else ''}</div>
          </td>
          <td class="rank-stars" style="color:{col['main']}">{stars:,}</td>
          <td class="rank-lang">{lang_name}</td>
          <td><div class="rank-bar"><div class="rank-bar-fill" style="width:{pct:.1f}%;background:{col['border']}"></div></div></td>
        </tr>""")
    ranking_rows = "\n".join(ranking_rows_lines)

    # ---- 分类占比行 ----
    max_cat_count = max(len(v) for v in cat_groups.values()) or 1
    distribution_lines = []
    for cat in sorted_cats:
        cnt = len(cat_groups[cat])
        col = resolve_category_colors(cat)
        pct = cnt / max_cat_count * 100
        distribution_lines.append(f"""      <div class="dist-item">
        <div class="dist-color" style="background:{col['main']}"></div>
        <div class="dist-name" style="color:{col['main']}">{cat}</div>
        <div class="dist-bar"><div class="dist-bar-fill" style="width:{pct:.1f}%;background:{col['main']}"></div></div>
        <div class="dist-count" style="color:{col['main']}">{cnt}</div>
      </div>""")
    distribution_rows = "\n".join(distribution_lines)

    # ---- 按分类分组的项目卡片 ----
    category_groups_lines = []
    for cat in sorted_cats:
        projs = cat_groups[cat]
        col = resolve_category_colors(cat)
        cards = []
        for p in projs:
            stars = p.get("stars", 0) or 0
            desc = p.get("description", "") or "暂无描述"
            full_name = p.get("full_name", p.get("name", ""))
            url = p.get("url", f"https://github.com/{full_name}")
            lang_tag = f'<span class="card-tag" style="background:{col["light"]};color:{col["main"]}">{p["language"]}</span>' if p.get("language") else ""

            cards.append(f"""        <div class="project-card">
          <div class="card-accent" style="background:{col['border']}"></div>
          <div class="card-body">
            <div class="card-top">
              <a href="{url}" class="card-name" style="color:{col['main']}" target="_blank" rel="noopener">{full_name}</a>
              <span class="card-stars" style="background:{col['light']};color:{col['main']}">
                <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.82 6.364a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
                {stars:,}
              </span>
            </div>
            <p class="card-desc">{desc}</p>
            <div class="card-footer">
              {lang_tag}
              <a href="{url}" class="card-link" target="_blank" rel="noopener">GitHub ↗</a>
            </div>
          </div>
        </div>""")

        card_grid = "\n".join(cards)
        category_groups_lines.append(f"""    <div class="category-group">
      <div class="category-head" style="background:{col['light']};border-left:4px solid {col['border']}">
        <div class="category-head-dot" style="background:{col['main']}"></div>
        <div class="category-head-name" style="color:{col['main']}">{cat}</div>
        <div class="category-head-count">{len(projs)} 个项目</div>
      </div>
      <div class="card-grid">
{card_grid}
      </div>
    </div>""")
    category_groups = "\n".join(category_groups_lines)

    html = HTML_TEMPLATE.format(
        lang=lang,
        title=title,
        count=count,
        total_stars=f"{total_stars:,}",
        avg_stars=avg_stars,
        cat_count=cat_count,
        ranking_rows=ranking_rows,
        distribution_rows=distribution_rows,
        category_groups=category_groups,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Project List — 项目汇总 HTML 生成器")
    parser.add_argument("--output", "-o", default=None, help="输出 HTML 路径（默认: ./github-projects-list.html）")
    parser.add_argument("--title", "-t", default="GitHub 项目汇总", help="页面标题")
    parser.add_argument("--language", "-l", choices=["zh", "en"], default="zh", help="页面语言")
    parser.add_argument("--open", action="store_true", help="生成后自动在浏览器中打开")
    args = parser.parse_args()

    projects = load_projects()
    if not projects:
        print(f"[!] 没有找到项目数据。请先使用 github_report.py 搜索至少一个 GitHub 项目。")
        print(f"    项目索引路径: {TRACKING_FILE}")
        return 1

    html = render_html(projects, args.title, args.language)

    output_path = Path(args.output) if args.output else Path.cwd() / "github-projects-list.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"[✓] 项目列表已生成: {output_path}")
    print(f"    共 {len(projects)} 个项目，{len({p.get('category','未分类') or '未分类' for p in projects})} 个分类")

    if args.open:
        webbrowser.open(str(output_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
