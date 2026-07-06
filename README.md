# GitHub Project Report Skill

> **创建时间**：2026-07-06 17:20  
> **最后修改时间**：2026-07-06 17:20  
> **当前版本**：V_1.1  
> **适用对象**：AI 智能体、开发者、技术调研者、项目分析师  
> **核心目标**：提供一套「搜索即归档」的 GitHub 项目调研工具 — 搜索任意 GitHub 开源项目，自动采集关键信息并生成结构化数据文件；同时将每次搜索的历史项目汇总为一个带分类配色、搜索筛选功能的可视化 HTML 列表，方便横向对比和管理项目收藏。  
> **文档简述**：本文档面向人类读者，完整覆盖 github-project-report-skill 的定位、功能、安装、用法、配色方案和常见问题，帮助快速上手并高效使用。

---

## 目录

- [简介](#简介)
- [包文件结构](#包文件结构)
- [核心功能](#核心功能)
- [快速开始](#快速开始)
- [脚本使用指南](#脚本使用指南)
  - [github_report.py — 项目信息采集器](#github_reportpy--项目信息采集器)
  - [github_list.py — 搜索历史汇总列表](#github_listpy--搜索历史汇总列表)
- [分类配色方案](#分类配色方案)
- [统一布局说明](#统一布局说明)
- [数据缓存与追踪](#数据缓存与追踪)
- [安装到 TRAE 平台](#安装到-trae-平台)
- [常见问题](#常见问题)
- [版本变更记录](#版本变更记录)

---

## 简介

### 这是什么？

GitHub Project Report Skill 是一个由两个 Python 脚本协作组成的 **GitHub 项目调研工具集**。它的核心工作流是：**搜索 → 采集 → 归档 → 可视化**。

### 解决了什么问题？

| 场景 | 问题 | 本工具的解法 |
|------|------|-------------|
| **技术选型调研** | 想快速了解一个开源项目，但手动翻 README、找配置、看目录结构太耗时 | `github_report.py` 一键采集所有关键信息并结构化输出 |
| **多个项目对比** | 调研了十几个项目，过几天就忘了各自特点和 Stars 数据 | `github_list.py` 自动归档每次搜索，生成带分类和排序的 HTML 列表 |
| **项目收藏管理** | 收藏的书签零散分散，没有统一的查看和管理入口 | 所有搜索记录自动累计，按分类配色展示，支持搜索和筛选 |
| **团队知识沉淀** | 做了项目调研但没有记录沉淀，下次别人又要重做一遍 | 每个项目保留 JSON 原始数据 + Markdown 摘要，可复用、可分享 |

### 双脚本协作流程

```
┌──────────────────────────────────────────────────────────────────────┐
│                   GitHub Project Report Skill                         │
│                                                                      │
│  github_report.py        ──→  原始数据（JSON）+ 摘要（MD）            │
│  (信息采集器)              ──→  自动写入 project_index.json（累计索引）  │
│                                                                      │
│                                ↓（读取索引）                           │
│                                                                      │
│  github_list.py           ──→  HTML 可视化列表                        │
│  (汇总生成器)              ──→  分类配色 / 搜索 / 筛选 / 排序          │
└──────────────────────────────────────────────────────────────────────┘
```

| 脚本 | 一句话职责 | 输入 | 输出 |
|------|-----------|------|------|
| `github_report.py` | **给一个 URL，还你一份结构化项目档案** | GitHub 仓库 URL + 选项 | JSON 原始数据 + Markdown 汇总 |
| `github_list.py` | **把历史搜索记录变成一张漂亮的卡片列表** | 无需输入（读取本地索引） | 自包含 HTML 页面 |

### 谁应该用？

- **开发者**：做技术调研、选型对比时快速了解多个开源项目
- **技术负责人 / 架构师**：追踪关注的项目动态，管理技术雷达
- **AI 智能体**：作为 TRAE Skill 自动执行，将 GitHub 项目信息提炼为结构化报告
- **项目经理 / 分析师**：做竞品分析、技术预研时沉淀可复用的调研档案

---

## 包文件结构

```
github-project-report-skill/
├── README.md                 ← 本文档
├── code/
│   ├── SKILL.md              ← 智能体调用指南（TRAE 平台 skill 定义）
│   ├── github_report.py      ← 项目信息采集器
│   └── github_list.py        ← 项目汇总列表生成器
```

安装到 TRAE 后：
```
.trae/skills/github-project-report-skill/
├── SKILL.md
├── github_report.py
└── github_list.py
```

缓存与追踪数据（自动生成）：
```
~/.cache/github-report-skill/
├── {url_hash}.json           # 按 URL SHA256 缓存的原始数据
└── project_index.json        # 累计项目索引（去重）
```

---

## 核心功能

### 单项目分析

- **元数据获取**：Stars、Forks、License、语言、Topics、默认分支
- **README 采集**：自动优先中文 README（`README_zh-CN.md` → `README_zh.md` → `README_CN.md` → `README.md`）
- **智能截断**：基于 Markdown H2 章节截断超长 README，保留核心内容
- **关键文件下载**：并发抓取 config、Makefile、pyproject.toml、Dockerfile 等 16+ 个关键文件
- **docs/ 文档探索**：自动发现并下载 docs/ 目录下的 Markdown 文档
- **目录结构**：获取仓库根目录文件列表
- **多输出格式**：JSON 原始数据 + Markdown 汇总 + 可路由到 HTML 报告生成
- **失败回退**：urllib → curl 自动降级，API 限流提示 Token，缓存兜底

### 跨项目汇总列表

- **卡片网格布局**：响应式网格，每张卡片包含项目名、简介、Stars、分类、语言、搜索时间
- **关键词搜索**：实时搜索项目名称、描述和完整路径
- **分类筛选**：根据项目分类下拉过滤
- **语言筛选**：根据编程语言下拉过滤
- **多维排序**：Stars 从高到低 / 从低到高、名称 AZ / ZA、最近搜索
- **分类配色**：12 套色系，每个分类有专属的卡片色条、标签、链接和按钮颜色
- **自动暗色模式**：跟随系统 `prefers-color-scheme` 自动切换深色/浅色主题
- **活动筛选标签**：显示当前过滤条件，单击 × 快速移除
- **零外部依赖**：单文件自包含 HTML，无 CDN、无第三方库

### 自动项目追踪

- 每次执行 `github_report.py` 自动将项目信息追加到累计索引
- 按 `full_name` 去重覆盖，数据始终保持最新
- 支持 `--category` 手动指定分类，或从 Topics/Language 自动推断

---

## 快速开始

以下用三个实际例子演示从「搜索单个项目」到「生成汇总列表」的完整链路。

### 第一步：搜索一个项目

```bash
python github_report.py https://github.com/vuejs/core -o ./vue-report
```

执行后，`./vue-report/` 目录下会生成：
- `collected_data.json` — 仓库元数据、README 全文、配置文件内容、目录结构
- `collected_summary.md` — 经过整理的信息汇总，可直接阅读

同时，该项目自动写入本地缓存索引（`~/.cache/github-report-skill/project_index.json`）。

### 第二步：搜索更多项目（带上分类标签）

```bash
python github_report.py https://github.com/tensorflow/tensorflow --category "machine-learning"
python github_report.py https://github.com/n8n-io/n8n --category "自动化"
python github_report.py https://github.com/lodash/lodash --category "javascript"
```

每次执行都会将项目追加到索引中。`--category` 参数指定分类，后续在列表页中会按此分类赋予对应的配色。

### 第三步：生成所有项目的汇总列表

```bash
python github_list.py --title "我的 GitHub 收藏" --open
```

- 读取索引中所有项目数据
- 生成 `./github-projects-list.html`
- `--open` 自动在浏览器中打开
- 页面上可实时搜索、按分类/语言筛选、按 Stars/名称排序

---

## 脚本使用指南

### github_report.py — 项目信息采集器

```bash
python github_report.py <github_url> [选项]
```

| 参数 | 简写 | 说明 |
|------|------|------|
| `url` | — | GitHub 仓库地址（必填） |
| `--output-dir` | `-o` | 输出目录（默认: `{repo}-report/`） |
| `--token` | `-t` | GitHub Personal Access Token（提高 API 限额） |
| `--verbose` | `-v` | 显示详细调试信息 |
| `--quiet` | `-q` | 仅显示错误信息 |
| `--no-cache` | — | 禁用本地缓存，强制刷新 |
| `--max-readme-chapters` | — | README 保留的最大章节数（默认 20） |
| `--format` | `-f` | 输出格式偏好：`json` / `md` / `html`（默认 `json`） |
| `--language` | `-l` | 输出语言：`zh` / `en`（默认 `zh`） |
| `--category` | `-c` | 项目分类标签（用于索引，默认自动推断） |
| `--no-track` | — | 不将本次搜索记录到项目索引中 |

**完整示例**：

```bash
# 基本用法
python github_report.py https://github.com/calesthio/OpenMontage

# 指定 Token 避免限流
python github_report.py https://github.com/calesthio/OpenMontage --token ghp_xxxx

# 指定分类和输出目录
python github_report.py https://github.com/vuejs/core -c "前端框架" -o ./vue-report -v

# 英文输出 + Markdown 格式
python github_report.py https://github.com/tensorflow/tensorflow -l en -f md

# 跳过索引追踪
python github_report.py https://github.com/lodash/lodash --no-track
```

### github_list.py — 搜索历史汇总列表

```bash
python github_list.py [选项]
```

| 参数 | 简写 | 说明 |
|------|------|------|
| `--output` | `-o` | 输出 HTML 路径（默认: `./github-projects-list.html`） |
| `--title` | `-t` | 页面标题（默认: `GitHub 项目收藏`） |
| `--sort` | — | 默认排序：`stars-desc` / `stars-asc` / `name-asc` / `name-desc` / `newest` |
| `--language` | `-l` | 页面语言：`zh` / `en` |
| `--open` | —  | 生成后自动在浏览器中打开 |

**完整示例**：

```bash
# 默认生成
python github_list.py

# 指定输出位置和标题
python github_list.py -o ./docs/my-projects.html --title "我的 GitHub 收藏"

# 默认按 Stars 从低到高排序
python github_list.py --sort stars-asc

# 生成后自动打开浏览器
python github_list.py --open
```

---

## 分类配色方案

本 Skill 内置了 **12 套分类专属配色**，覆盖常见项目领域。每套配色包含 `light`（浅底）、`main`（主色）、`border`（边线）三色，在卡片顶部色条、项目名称、Stars 徽章、分类标签、查看按钮上统一应用。

| 分类关键词 | 色系 | 浅色 | 主色 | 边线 |
|------------|------|------|------|------|
| 默认（fallback） | 沉稳蓝 | `#ebf4ff` | `#2b6cb0` | `#3182ce` |
| `ai` / `machine-learning` / `deep-learning` / `llm` | 科技紫 | `#f3e8ff` | `#7c3aed` | `#8b5cf6` |
| `前端框架` / `frontend` / `ui` | 亮蓝 | `#dbeafe` | `#2563eb` | `#3b82f6` |
| `javascript` | 琥珀金 | `#fef9c3` | `#a16207` | `#ca8a04` |
| `python` | 绿松 | `#d1fae5` | `#047857` | `#059669` |
| `backend` / `api` | 翠绿 | `#dcfce7` | `#16a34a` | `#22c55e` |
| `自动化` / `automation` / `devops` | 天蓝 | `#e0f2fe` | `#0284c7` | `#0ea5e9` |
| `data` / `database` | 玫瑰粉 | `#fce7f3` | `#be185d` | `#db2777` |
| `security` | 赤红 | `#fee2e2` | `#b91c1c` | `#dc2626` |
| `tools` / `cli` | 暖灰 | `#f5f5f4` | `#57534e` | `#78716c` |
| `game` | 橙 | `#ffedd5` | `#c2410c` | `#ea580c` |
| `未分类` | 石板灰 | `#f1f5f9` | `#475569` | `#64748b` |

**分类匹配规则**（优先级从高到低）：
1. 用户通过 `--category` 参数显式指定
2. 项目 Topics 列表的第一个标签
3. 项目主要编程语言
4. `未分类`

配色通过精确匹配和关键词模糊匹配双重机制查找，未匹配到的分类回退到默认蓝。

---

## 统一布局说明

生成的 HTML 列表页采用 **Design Tokens 设计系统**，所有组件使用一致的 CSS 变量：

| Token | 用途 |
|-------|------|
| `--bg` / `--card-bg` | 页面背景 / 卡片背景 |
| `--text` / `--text-secondary` / `--text-muted` | 三级文本色层级 |
| `--border` / `--shadow-*` | 边框与三级阴影体系 |
| `--radius` / `--radius-sm` / `--radius-lg` | 圆角体系 |
| `--font` / `--font-mono` | 正文字体 / 等宽字体 |

**页面组件结构**：

```
┌─ Header ─────────────────────────────────────┐
│  🌈 渐变色条 (4px)                           │
│  标题 + 统计 (项目数 / 筛选数 / 总Stars / 平均) │
└──────────────────────────────────────────────┘
┌─ Controls ───────────────────────────────────┐
│  🔍 搜索框  │  分类下拉  │  语言下拉  │  排序  │
└──────────────────────────────────────────────┘
┌─ 活动筛选标签 ──────────────────────────────┐
│  [分类: xxx ×]  [语言: xxx ×]  [搜索: xxx ×] │
└──────────────────────────────────────────────┘
┌─ Project Grid (响应式卡片) ────────────── ──┐
│  ┌── Card ──┐  ┌── Card ──┐  ┌── Card ──┐  │
│  │ ██ 色条  │  │ ██ 色条  │  │ ██ 色条  │  │
│  │ 项目名 ⭐ │  │ 项目名 ⭐ │  │ 项目名 ⭐ │  │
│  │ 简介     │  │ 简介     │  │ 简介     │  │
│  │ 分类 语言 │  │ 分类 语言 │  │ 分类 语言 │  │
│  │ [查看]   │  │ [查看]   │  │ [查看]   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└──────────────────────────────────────────────┘
```

---

## 数据缓存与追踪

### 缓存机制

- 缓存目录：`~/.cache/github-report-skill/`
- 缓存方式：按 URL SHA256 哈希值索引的 JSON 文件
- 默认启用缓存，重复分析同一项目时直接读取本地缓存
- 使用 `--no-cache` 强制刷新远程数据

### 项目追踪索引

- 索引文件：`~/.cache/github-report-skill/project_index.json`
- 每次执行 `github_report.py` 自动更新（除非指定 `--no-track`）
- 按 `full_name` 去重覆盖，同一仓库多次搜索只保留最新记录
- 索引数据直接供给 `github_list.py` 生成汇总列表

```json
{
  "version": "1.0",
  "count": 5,
  "projects": [
    {
      "name": "tensorflow",
      "full_name": "tensorflow/tensorflow",
      "description": "An Open Source Machine Learning Framework for Everyone",
      "stars": 188000,
      "forks": 74000,
      "language": "Python",
      "topics": ["machine-learning", "deep-learning"],
      "category": "machine-learning",
      "url": "https://github.com/tensorflow/tensorflow",
      "searched_at": "2026-07-03T09:15:00"
    }
  ]
}
```

---

## 安装到 TRAE 平台

该 Skill 默认已安装到 TRAE 平台，安装位置为：

```
.trae/skills/github-project-report-skill/
├── SKILL.md
├── github_report.py
└── github_list.py
```

如需重新安装，将 `code/` 目录下的三个文件复制到 `.trae/skills/github-project-report-skill/` 即可。

系统会通过 `SKILL.md` 中的 `name` 和 `description` 元数据自动识别并匹配用户输入，当用户提供 GitHub 链接要求"做简介/报告/教程/入门/分析/总结"时自动激活。

---

## 常见问题

### Q: 遇到 GitHub API 403 限流怎么办？

使用 `--token` 参数传入 Personal Access Token，API 限额将从 60 次/小时提升到 5000 次/小时。

### Q: 怎么更新某个项目的分类？

重新执行 `github_report.py` 并指定新的 `--category`，会自动覆盖索引中的旧分类。

### Q: 怎么删除某个不需要的项目？

直接编辑 `~/.cache/github-report-skill/project_index.json`，移除对应的项目对象，然后重新运行 `github_list.py`。

### Q: 为什么我生成的列表页没有颜色？

检查项目是否有分类（`--category` 参数），如果没有分类则使用默认配色（沉稳蓝）。分类字段为空会显示为"未分类"并匹配石板灰色系。

### Q: 生成的 HTML 可以离线使用吗？

可以。HTML 是单文件自包含的，所有样式、图标都内联在文件中，无任何外部依赖。

### Q: 搜索一个项目后我改主意了不想计入索引怎么办？

使用 `--no-track` 参数即可跳过索引记录。

---

## 版本变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| V_1.0 | 2026-07-06 | 初始版本：信息采集 + SKILL.md 定义 |
| V_1.1 | 2026-07-06 | 新增 `github_list.py` 项目汇总列表（分类配色、统一布局、搜索筛选）；`github_report.py` 增加 `--category` / `--no-track` 参数和自动追踪逻辑；更新 SKILL.md |
