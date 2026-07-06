#!/usr/bin/env python3
"""
GitHub Project List — 搜索历史项目汇总 HTML 生成器（统一布局 + 分类配色）

用法:
    python github_list.py [选项]

示例:
    python github_list.py                                              # 生成到 ./github-projects-list.html
    python github_list.py -o ./output/my-projects.html                 # 指定输出路径
    python github_list.py --title "我的 GitHub 收藏"                    # 自定义标题
    python github_list.py --sort stars-desc                            # 默认排序方式
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
# 按领域 / 内容风格定义不同色系，卡片顶部色条、标签、链接均使用对应配色
CATEGORY_COLORS: dict[str, dict[str, str]] = {
    # 默认色 —— 沉稳蓝
    "default": {
        "light": "#ebf4ff", "main": "#2b6cb0", "border": "#3182ce",
        "dark": "#60a5fa", "dark_light": "#1e3a5f",
    },
    # AI / 机器学习 / 深度学习 —— 科技紫
    "ai": {
        "light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6",
        "dark": "#a78bfa", "dark_light": "#2e1065",
    },
    "machine-learning": {
        "light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6",
        "dark": "#a78bfa", "dark_light": "#2e1065",
    },
    "deep-learning": {
        "light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6",
        "dark": "#a78bfa", "dark_light": "#2e1065",
    },
    "llm": {
        "light": "#f3e8ff", "main": "#7c3aed", "border": "#8b5cf6",
        "dark": "#a78bfa", "dark_light": "#2e1065",
    },
    # 前端 / UI —— 亮蓝
    "前端框架": {
        "light": "#dbeafe", "main": "#2563eb", "border": "#3b82f6",
        "dark": "#60a5fa", "dark_light": "#1e3a5f",
    },
    "frontend": {
        "light": "#dbeafe", "main": "#2563eb", "border": "#3b82f6",
        "dark": "#60a5fa", "dark_light": "#1e3a5f",
    },
    "ui": {
        "light": "#dbeafe", "main": "#2563eb", "border": "#3b82f6",
        "dark": "#60a5fa", "dark_light": "#1e3a5f",
    },
    # JavaScript —— 琥珀金
    "javascript": {
        "light": "#fef9c3", "main": "#a16207", "border": "#ca8a04",
        "dark": "#fde047", "dark_light": "#422006",
    },
    # Python —— 绿松
    "python": {
        "light": "#d1fae5", "main": "#047857", "border": "#059669",
        "dark": "#34d399", "dark_light": "#022c22",
    },
    # 后端 / API —— 翠绿
    "backend": {
        "light": "#dcfce7", "main": "#16a34a", "border": "#22c55e",
        "dark": "#4ade80", "dark_light": "#052e16",
    },
    # 自动化 / DevOps —— 天蓝
    "自动化": {
        "light": "#e0f2fe", "main": "#0284c7", "border": "#0ea5e9",
        "dark": "#38bdf8", "dark_light": "#0c4a6e",
    },
    "automation": {
        "light": "#e0f2fe", "main": "#0284c7", "border": "#0ea5e9",
        "dark": "#38bdf8", "dark_light": "#0c4a6e",
    },
    "devops": {
        "light": "#e0f2fe", "main": "#0284c7", "border": "#0ea5e9",
        "dark": "#38bdf8", "dark_light": "#0c4a6e",
    },
    # 数据 / 数据库 —— 玫瑰粉
    "data": {
        "light": "#fce7f3", "main": "#be185d", "border": "#db2777",
        "dark": "#f472b6", "dark_light": "#4c0519",
    },
    "database": {
        "light": "#fce7f3", "main": "#be185d", "border": "#db2777",
        "dark": "#f472b6", "dark_light": "#4c0519",
    },
    # 安全 —— 赤红
    "security": {
        "light": "#fee2e2", "main": "#b91c1c", "border": "#dc2626",
        "dark": "#f87171", "dark_light": "#450a0a",
    },
    # 工具 / CLI —— 暖灰
    "tools": {
        "light": "#f5f5f4", "main": "#57534e", "border": "#78716c",
        "dark": "#a8a29e", "dark_light": "#1c1917",
    },
    "cli": {
        "light": "#f5f5f4", "main": "#57534e", "border": "#78716c",
        "dark": "#a8a29e", "dark_light": "#1c1917",
    },
    # 游戏 —— 橙
    "game": {
        "light": "#ffedd5", "main": "#c2410c", "border": "#ea580c",
        "dark": "#fb923c", "dark_light": "#431407",
    },
    # 未分类 —— 石板灰
    "未分类": {
        "light": "#f1f5f9", "main": "#475569", "border": "#64748b",
        "dark": "#94a3b8", "dark_light": "#1e293b",
    },
}


def resolve_category_colors(category: str) -> dict[str, str]:
    """根据分类名查找配色方案，找不到则用默认。"""
    key = (category or "").strip().lower()
    if key in CATEGORY_COLORS:
        return CATEGORY_COLORS[key]
    # 模糊匹配：包含关键词
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
/* ========== Design Tokens ========== */
:root {{
  --bg: #f0f2f5;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #5a5a7a;
  --text-muted: #8e8ea0;
  --border: #e2e5ec;
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04);
  --shadow: 0 2px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 8px 30px rgba(0,0,0,0.08);
  --radius: 12px;
  --radius-sm: 8px;
  --radius-lg: 16px;
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
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
    --shadow: 0 2px 12px rgba(0,0,0,0.3);
    --shadow-lg: 0 8px 30px rgba(0,0,0,0.4);
  }}
}}

/* ========== Reset & Base ========== */
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

.container {{ max-width: 1240px; margin: 0 auto; padding: 28px 20px 60px; }}

/* ========== Header ========== */
.header {{
  text-align: center;
  margin-bottom: 32px;
  padding: 48px 28px 36px;
  background: var(--card-bg);
  border-radius: var(--radius-lg);
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
.header h1 {{
  font-size: 1.85rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}}
.header .subtitle {{
  color: var(--text-secondary);
  font-size: 0.95rem;
}}

/* Stats Row */
.stats-row {{
  display: flex;
  justify-content: center;
  gap: 36px;
  margin-top: 24px;
  flex-wrap: wrap;
}}
.stat-item {{
  text-align: center;
}}
.stat-number {{
  font-size: 1.65rem;
  font-weight: 700;
  color: #2b6cb0;
}}
.stat-label {{
  font-size: 0.78rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-top: 2px;
}}
@media (prefers-color-scheme: dark) {{
  .stat-number {{ color: #60a5fa; }}
}}

/* ========== Controls ========== */
.controls {{
  display: flex;
  gap: 10px;
  margin-bottom: 28px;
  flex-wrap: wrap;
  align-items: center;
  background: var(--card-bg);
  padding: 14px 18px;
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}}
.controls input,
.controls select {{
  padding: 9px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg);
  color: var(--text);
  font-size: 0.88rem;
  font-family: var(--font);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}}
.controls input:focus,
.controls select:focus {{
  border-color: #2b6cb0;
  box-shadow: 0 0 0 3px rgba(43,108,176,0.12);
}}
@media (prefers-color-scheme: dark) {{
  .controls input:focus,
  .controls select:focus {{
    border-color: #60a5fa;
    box-shadow: 0 0 0 3px rgba(96,165,250,0.15);
  }}
}}
.search-box {{
  flex: 1 1 240px;
  min-width: 180px;
  padding-left: 36px !important;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%238e8ea0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='M21 21l-4.35-4.35'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-size: 16px;
  background-position: 12px center;
}}
.filter-group {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}
.sort-group {{
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  font-size: 0.84rem;
  color: var(--text-secondary);
}}
.sort-group select {{ min-width: 125px; }}

/* Filter Count Badge */
.filter-badge {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 0.78rem;
  color: var(--text-secondary);
  white-space: nowrap;
}}

/* ========== Project Grid ========== */
.project-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 18px;
}}
@media (max-width: 480px) {{
  .project-grid {{ grid-template-columns: 1fr; gap: 14px; }}
}}

/* ========== Project Card ========== */
.project-card {{
  background: var(--card-bg);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}}
.project-card:hover {{
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}}

/* Category color accent strip */
.card-accent {{
  height: 4px;
  width: 100%;
  flex-shrink: 0;
  transition: height 0.2s ease;
}}
.project-card:hover .card-accent {{
  height: 5px;
}}

.card-body {{
  padding: 18px 20px 14px;
  display: flex;
  flex-direction: column;
  flex: 1;
}}

.card-header {{
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}}
.project-name {{
  font-size: 1.05rem;
  font-weight: 600;
  text-decoration: none;
  word-break: break-all;
  line-height: 1.35;
}}
.project-name:hover {{
  text-decoration: underline;
}}

.stars-badge {{
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  line-height: 1.4;
}}
.stars-badge svg {{
  width: 14px;
  height: 14px;
  flex-shrink: 0;
}}

.project-description {{
  color: var(--text-secondary);
  font-size: 0.87rem;
  line-height: 1.55;
  margin-bottom: 12px;
  flex: 1;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}

/* Card footer with tags */
.card-footer {{
  display: flex;
  align-items: center;
  gap: 7px;
  flex-wrap: wrap;
  margin-top: auto;
  padding-top: 10px;
  border-top: 1px solid var(--border);
}}
.tag {{
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.74rem;
  font-weight: 500;
  line-height: 1.5;
}}
.tag.category {{
  font-weight: 600;
}}
.tag.language {{
  background: var(--bg);
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 0.72rem;
}}
.searched-at {{
  margin-left: auto;
  font-size: 0.7rem;
  color: var(--text-muted);
}}

/* View button */
.project-link-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 500;
  text-decoration: none;
  margin: 0 20px 16px;
  transition: opacity 0.2s;
}}
.project-link-btn:hover {{
  opacity: 0.88;
}}
.project-link-btn svg {{
  width: 15px;
  height: 15px;
}}

/* ========== Empty State ========== */
.empty-state {{
  text-align: center;
  padding: 70px 20px;
  color: var(--text-muted);
  display: none;
}}
.empty-state svg {{
  width: 60px;
  height: 60px;
  margin-bottom: 16px;
  opacity: 0.3;
}}
.empty-state h3 {{ font-size: 1.1rem; color: var(--text-secondary); margin-bottom: 6px; }}

/* ========== Active Filter Tags ========== */
.active-filters {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 18px;
  min-height: 0;
}}
.active-filter-tag {{
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 12px 3px 14px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 20px;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
}}
.active-filter-tag:hover {{
  border-color: #dc2626;
  color: #dc2626;
}}
.active-filter-tag .close {{
  font-size: 1.1rem;
  line-height: 1;
}}

/* ========== Footer ========== */
.footer {{
  text-align: center;
  margin-top: 48px;
  padding: 20px;
  color: var(--text-muted);
  font-size: 0.78rem;
}}
.footer a {{ color: var(--text-secondary); text-decoration: underline; }}
.footer a:hover {{ color: var(--text); }}
</style>
</head>
<body>
<div class="container">
  <!-- Header -->
  <header class="header">
    <h1>{title}</h1>
    <p class="subtitle">共 <strong id="total-count">{count}</strong> 个项目，累计 <strong id="total-stars">{total_stars}</strong> ⭐</p>
    <div class="stats-row">
      <div class="stat-item">
        <div class="stat-number">{count}</div>
        <div class="stat-label">项目总数</div>
      </div>
      <div class="stat-item">
        <div class="stat-number" id="live-count">{count}</div>
        <div class="stat-label">当前筛选</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{total_stars}</div>
        <div class="stat-label">总 Stars</div>
      </div>
      <div class="stat-item">
        <div class="stat-number">{avg_stars}</div>
        <div class="stat-label">平均 Stars</div>
      </div>
    </div>
  </header>

  <!-- Controls -->
  <div class="controls">
    <input type="text" class="search-box" id="searchInput" placeholder="搜索项目名称或描述..." oninput="filterProjects()">
    <div class="filter-group">
      <select id="categoryFilter" onchange="filterProjects()">
        <option value="">所有分类</option>
{category_options}
      </select>
      <select id="languageFilter" onchange="filterProjects()">
        <option value="">所有语言</option>
{language_options}
      </select>
    </div>
    <div class="sort-group">
      <label for="sortSelect">排序</label>
      <select id="sortSelect" onchange="filterProjects()">
        <option value="stars-desc" {sort_sd}>Stars 从高到低</option>
        <option value="stars-asc" {sort_sa}>Stars 从低到高</option>
        <option value="name-asc" {sort_na}>名称 A-Z</option>
        <option value="name-desc" {sort_nd}>名称 Z-A</option>
        <option value="newest" {sort_ne}>最近搜索</option>
      </select>
    </div>
  </div>

  <!-- Active Filters -->
  <div class="active-filters" id="activeFilters"></div>

  <!-- Project Cards -->
  <div class="project-grid" id="projectGrid">
{project_cards}
  </div>

  <!-- Empty State -->
  <div class="empty-state" id="emptyState">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/>
    </svg>
    <h3>没有找到匹配的项目</h3>
    <p>试试调整筛选条件或搜索关键词</p>
  </div>

  <!-- Footer -->
  <div class="footer">
    <p>生成于 {generated_at} · <a href="https://github.com" target="_blank" rel="noopener">GitHub</a></p>
  </div>
</div>

<script>
// ========== Data ==========
const projects = {projects_json};
const categoryColors = {category_colors_json};

// ========== Category Color Helpers ==========
function getCatColor(cat) {{
  const key = (cat || '').toLowerCase().trim();
  return categoryColors[key] || categoryColors['default'];
}}

function getStarsColor(cat) {{
  const c = getCatColor(cat);
  return c.main;
}}

function getStarsBg(cat) {{
  const c = getCatColor(cat);
  return c.light;
}}

// ========== Render ==========
function renderStarsCount(n) {{
  if (n >= 1000) return (n / 1000).toFixed(1).replace('.0', '') + 'k';
  return n.toLocaleString();
}}

function filterProjects() {{
  const search = document.getElementById('searchInput').value.toLowerCase().trim();
  const category = document.getElementById('categoryFilter').value;
  const lang = document.getElementById('languageFilter').value;
  const sort = document.getElementById('sortSelect').value;

  // Filter
  let filtered = projects.filter(function(p) {{
    if (category && p.category !== category) return false;
    if (lang && (p.language || '') !== lang) return false;
    if (search) {{
      var name = (p.name || '').toLowerCase();
      var desc = (p.description || '').toLowerCase();
      var full = (p.full_name || '').toLowerCase();
      if (name.indexOf(search) === -1 && desc.indexOf(search) === -1 && full.indexOf(search) === -1) return false;
    }}
    return true;
  }});

  // Sort
  filtered.sort(function(a, b) {{
    switch (sort) {{
      case 'stars-asc': return (a.stars || 0) - (b.stars || 0);
      case 'name-asc': return (a.name || '').localeCompare(b.name || '');
      case 'name-desc': return (b.name || '').localeCompare(a.name || '');
      case 'newest': return new Date(b.searched_at || 0) - new Date(a.searched_at || 0);
      default: return (b.stars || 0) - (a.stars || 0);
    }}
  }});

  // Render cards
  var grid = document.getElementById('projectGrid');
  var html = '';
  for (var i = 0; i < filtered.length; i++) {{
    var p = filtered[i];
    var stars = p.stars || 0;
    var desc = p.description || '暂无描述';
    var col = getCatColor(p.category);
    var langTag = p.language ? '<span class="tag language">' + escHtml(p.language) + '</span>' : '';
    var catTag = p.category ? '<span class="tag category" style="background:' + col.light + ';color:' + col.main + '">' + escHtml(p.category) + '</span>' : '';
    var when = p.searched_at ? new Date(p.searched_at).toLocaleDateString() : '';
    var fullName = p.full_name || p.name;
    var url = p.url || 'https://github.com/' + fullName;

    html += '<div class="project-card">' +
      '<div class="card-accent" style="background:' + col.border + '"></div>' +
      '<div class="card-body">' +
        '<div class="card-header">' +
          '<a href="' + escAttr(url) + '" class="project-name" style="color:' + col.main + '" target="_blank" rel="noopener">' + escHtml(fullName) + '</a>' +
          '<span class="stars-badge" style="background:' + col.light + ';color:' + col.main + '">' +
            '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.82 6.364a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>' +
            renderStarsCount(stars) +
          '</span>' +
        '</div>' +
        '<p class="project-description">' + escHtml(desc) + '</p>' +
        '<div class="card-footer">' + catTag + langTag +
          '<span class="searched-at">' + when + '</span>' +
        '</div>' +
      '</div>' +
      '<a href="' + escAttr(url) + '" class="project-link-btn" style="background:' + col.main + ';color:#fff" target="_blank" rel="noopener">' +
        '<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.58-.01 1.01.54 1.15.76.69 1.17 1.78.83 2.22.63.07-.5.28-.83.51-1.02-1.71-.19-3.51-.86-3.51-3.82 0-.84.3-1.53.79-2.07-.08-.2-.34-1.01.07-2.1 0 0 .64-.21 2.12.79a7.4 7.4 0 014 0c1.47-1 2.12-.79 2.12-.79.41 1.09.15 1.9.07 2.1.49.54.79 1.23.79 2.07 0 2.97-1.81 3.63-3.53 3.82.28.24.53.72.53 1.46 0 1.05-.01 1.9-.01 2.16 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>' +
        '查看项目' +
      '</a>' +
    '</div>';
  }}
  grid.innerHTML = html;

  // Update stats
  document.getElementById('live-count').textContent = filtered.length;
  document.getElementById('emptyState').style.display = filtered.length === 0 ? 'block' : 'none';

  // Active filter tags
  var tags = document.getElementById('activeFilters');
  var tagHtml = '';
  if (category) tagHtml += '<span class="active-filter-tag" onclick="document.getElementById(\'categoryFilter\').value=\'\';filterProjects()">分类: ' + escHtml(category) + ' <span class="close">&times;</span></span>';
  if (lang) tagHtml += '<span class="active-filter-tag" onclick="document.getElementById(\'languageFilter\').value=\'\';filterProjects()">语言: ' + escHtml(lang) + ' <span class="close">&times;</span></span>';
  if (search) tagHtml += '<span class="active-filter-tag" onclick="document.getElementById(\'searchInput\').value=\'\';filterProjects()">搜索: "' + escHtml(search) + '" <span class="close">&times;</span></span>';
  tags.innerHTML = tagHtml;
}}

function escHtml(s) {{
  if (!s) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}}
function escAttr(s) {{
  return String(s).replace(/"/g, '&quot;').replace(/&/g, '&amp;');
}}

// ========== Init ==========
filterProjects();
</script>
</body>
</html>
"""


def _build_category_colors_json(categories: list[str]) -> str:
    """构建前端用的分类配色映射 JSON。"""
    result = {"default": CATEGORY_COLORS["default"]}
    for cat in categories:
        colors = resolve_category_colors(cat)
        key = (cat or "").strip().lower()
        result[key] = colors
    return json.dumps(result, ensure_ascii=False)


def load_projects() -> list[dict]:
    """加载项目追踪数据。"""
    if not TRACKING_FILE.exists():
        return []
    try:
        data = json.loads(TRACKING_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("projects", [])
    except Exception:
        return []


def render_html(projects: list[dict], title: str, sort_default: str, lang: str) -> str:
    """渲染 HTML 页面。"""
    total_stars = sum(p.get("stars", 0) or 0 for p in projects)
    count = len(projects)
    avg_stars = round(total_stars / count) if count > 0 else 0

    # 提取分类和语言
    categories = sorted({p.get("category", "未分类") for p in projects if p.get("category")})
    languages = sorted({p.get("language") for p in projects if p.get("language")})

    category_options = "\n".join(
        f'        <option value="{c}">{c}</option>' for c in categories
    )
    language_options = "\n".join(
        f'        <option value="{l}">{l}</option>' for l in languages
    )

    # 分类配色映射
    category_colors_json = _build_category_colors_json(categories)

    # 排序选项选中状态
    sf = {"sd": "", "sa": "", "na": "", "nd": "", "ne": ""}
    sort_key_map = {"stars-desc": "sd", "stars-asc": "sa", "name-asc": "na", "name-desc": "nd", "newest": "ne"}
    sk = sort_key_map.get(sort_default, "sd")
    sf[sk] = 'selected'

    # 首屏卡片渲染（按 stars 倒序）
    project_cards_lines = []
    sorted_projects = sorted(projects, key=lambda p: -(p.get("stars", 0) or 0))
    for p in sorted_projects:
        stars = p.get("stars", 0) or 0
        desc = p.get("description", "") or "暂无描述"
        cat = p.get("category", "")
        colors = resolve_category_colors(cat)
        full_name = p.get("full_name", p.get("name", ""))
        url = p.get("url", f"https://github.com/{full_name}")
        when = ""
        if p.get("searched_at"):
            try:
                when = datetime.fromisoformat(p["searched_at"]).strftime("%Y-%m-%d")
            except Exception:
                pass

        lang_tag = f'<span class="tag language">{p["language"]}</span>' if p.get("language") else ""
        cat_tag = f'<span class="tag category" style="background:{colors["light"]};color:{colors["main"]}">{cat}</span>' if cat else ""

        card = f"""    <div class="project-card">
        <div class="card-accent" style="background:{colors['border']}"></div>
        <div class="card-body">
          <div class="card-header">
            <a href="{url}" class="project-name" style="color:{colors['main']}" target="_blank" rel="noopener">{full_name}</a>
            <span class="stars-badge" style="background:{colors['light']};color:{colors['main']}">
              <svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 01.673.418l1.882 3.815 4.21.612a.75.75 0 01.416 1.279l-3.046 2.97.719 4.192a.75.75 0 01-1.088.791L8 12.347l-3.766 1.98a.75.75 0 01-1.088-.79l.72-4.194L.82 6.364a.75.75 0 01.416-1.28l4.21-.611L7.327.668A.75.75 0 018 .25z"/></svg>
              {stars:,}
            </span>
          </div>
          <p class="project-description">{desc}</p>
          <div class="card-footer">
            {cat_tag}
            {lang_tag}
            <span class="searched-at">{when}</span>
          </div>
        </div>
        <a href="{url}" class="project-link-btn" style="background:{colors['main']};color:#fff" target="_blank" rel="noopener">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.58-.01 1.01.54 1.15.76.69 1.17 1.78.83 2.22.63.07-.5.28-.83.51-1.02-1.71-.19-3.51-.86-3.51-3.82 0-.84.3-1.53.79-2.07-.08-.2-.34-1.01.07-2.1 0 0 .64-.21 2.12.79a7.4 7.4 0 014 0c1.47-1 2.12-.79 2.12-.79.41 1.09.15 1.9.07 2.1.49.54.79 1.23.79 2.07 0 2.97-1.81 3.63-3.53 3.82.28.24.53.72.53 1.46 0 1.05-.01 1.9-.01 2.16 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
          查看项目
        </a>
      </div>"""
        project_cards_lines.append(card)

    project_cards = "\n".join(project_cards_lines)

    # JS 用的 projects JSON
    projects_json = json.dumps(
        [
            {
                "name": p.get("name"),
                "full_name": p.get("full_name"),
                "description": p.get("description"),
                "stars": p.get("stars", 0) or 0,
                "language": p.get("language"),
                "category": p.get("category", "未分类"),
                "url": p.get("url"),
                "searched_at": p.get("searched_at"),
            }
            for p in projects
        ],
        ensure_ascii=False,
    )

    html = HTML_TEMPLATE.format(
        lang=lang,
        title=title,
        count=count,
        total_stars=f"{total_stars:,}",
        avg_stars=avg_stars,
        category_options=category_options,
        language_options=language_options,
        category_colors_json=category_colors_json,
        sort_sd=sf["sd"], sort_sa=sf["sa"], sort_na=sf["na"], sort_nd=sf["nd"], sort_ne=sf["ne"],
        project_cards=project_cards,
        projects_json=projects_json,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    return html


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GitHub Project List — 搜索历史项目汇总 HTML 生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python github_list.py
  python github_list.py -o ./my-list.html
  python github_list.py --title "我的 GitHub 项目收藏"
  python github_list.py --sort stars-asc
  python github_list.py --open
        """,
    )
    parser.add_argument("--output", "-o", default=None, help="输出 HTML 文件路径（默认: ./github-projects-list.html）")
    parser.add_argument("--title", "-t", default="GitHub 项目收藏", help="页面标题（默认: GitHub 项目收藏）")
    parser.add_argument("--sort", default="stars-desc", choices=["stars-desc", "stars-asc", "name-asc", "name-desc", "newest"], help="默认排序方式（默认: stars-desc）")
    parser.add_argument("--language", "-l", choices=["zh", "en"], default="zh", help="页面语言（默认 zh）")
    parser.add_argument("--open", action="store_true", help="生成后自动在浏览器中打开")
    args = parser.parse_args()

    projects = load_projects()
    if not projects:
        print(f"[!] 没有找到项目数据。请先使用 github_report.py 搜索至少一个 GitHub 项目。")
        print(f"    项目索引路径: {TRACKING_FILE}")
        return 1

    html = render_html(projects, args.title, args.sort, args.language)

    output_path = Path(args.output) if args.output else Path.cwd() / "github-projects-list.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    print(f"[✓] 项目列表已生成: {output_path}")
    print(f"    共 {len(projects)} 个项目")

    if args.open:
        webbrowser.open(str(output_path))

    return 0


if __name__ == "__main__":
    sys.exit(main())
