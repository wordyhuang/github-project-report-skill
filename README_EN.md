# GitHub Project Report Skill

> 🌐 **中文** · [阅读中文版](README.md)

---

## Table of Contents

- [What is this skill?](#what-is-this-skill)
- [Capabilities Overview](#capabilities-overview)
- [File Structure](#file-structure)
- [Install into Your Agent](#install-into-your-agent)
- [How Your Agent Triggers It](#how-your-agent-triggers-it)
- [Generated Outputs](#generated-outputs)
- [Data Notes](#data-notes)

---

## What is this skill?

**GitHub Project Report Skill** is an agent skill. Once installed, your agent gains the following ability:

> Give it a GitHub repository link, and it will automatically fetch the project's metadata, README, config files, documentation, and directory structure — then distill everything into a structured report (HTML or Markdown). Every project you search is automatically recorded, so you can ask your agent to generate a visual card gallery with category-based colors, search, filtering, and sorting at any time.

In short: **search once, archived forever**.

## Capabilities Overview

| Capability | Description |
|------------|-------------|
| **Single Project Analysis** | Given a GitHub URL, auto-collect Stars/Forks/README/config/docs/directory structure, output structured JSON and summary Markdown |
| **Cross-Project Gallery** | Aggregate all searched GitHub projects into a self-contained HTML card page with search, category/language filtering, and multiple sort modes |
| **Category Colors** | Each category (AI, frontend, backend, automation, etc.) gets its own color scheme — accent strips, tags, links, and buttons all match |
| **Auto Tracking** | Every search is automatically accumulated into an index with deduplication — no manual management needed |

## File Structure

```
github-project-report-skill/
├── README.md                ← Chinese documentation
├── README_EN.md             ← English documentation (this file)
├── code/
│   ├── SKILL.md             ← Agent instruction guide (tells the agent how to use this skill)
│   ├── github_report.py     ← Project info collector (called by the agent)
│   └── github_list.py       ← Project gallery generator (called by the agent)
```

## Install into Your Agent

### Method 1: One-Sentence Install (Recommended)

Copy and send the prompt below to your agent — it will handle the rest:

> Please install the GitHub Project Report Skill. Get the three files SKILL.md, github_report.py, and github_list.py from the code/ directory of the GitHub repository wordyhuang/github-project-report-skill, and place them in the correct location according to your platform's skill installation conventions. Tell me the directory structure and installation result when done.

What the agent will do automatically:
1. Read the three files from the GitHub repository
2. Determine the correct installation path based on its own platform conventions
3. Write the files and confirm completion

> **Note**: Different platforms (TRAE, Cursor, Claude, custom Agents, etc.) have different skill directories — the agent knows where to put them. If the installation location is not what you expected, just tell the agent to move them.

### Method 2: Manual Copy

If you prefer to do it yourself, the skill is open-sourced at [wordyhuang/github-project-report-skill](https://github.com/wordyhuang/github-project-report-skill). Copy the three files from `code/` into your platform's skill directory:

| File | Description |
|------|-------------|
| `code/SKILL.md` | Agent instruction guide (tells the agent how to use this skill) |
| `code/github_report.py` | Project info collector |
| `code/github_list.py` | Project gallery generator |

## How Your Agent Triggers It

Once installed, the skill activates automatically when your agent receives any of these instructions:

- A GitHub repository link is provided with a request for "introduction / report / tutorial / getting started"
- A request to "analyze / summarize / extract info from a GitHub project"
- A request to "turn a GitHub project into a report / document"
- A request to "show all searched projects" or "generate a project gallery"
- Keywords containing `github.com` combined with `report | intro | tutorial | analyze | summary`

**Example triggers**:

```
Can you take a look at this project: https://github.com/vuejs/core
Show me a gallery of all the GitHub projects I've searched
Analyze the tensorflow/tensorflow repository
```

## Generated Outputs

After the agent uses this skill, the following files may be generated:

| File | Description |
|------|-------------|
| `{project-name}-report/collected_data.json` | Raw collected data for a single project (metadata, full README, config files, etc.) |
| `{project-name}-report/collected_summary.md` | Summary Markdown for a single project |
| `github-projects-list.html` | Visual card gallery of all searched projects (with search, filtering, sorting) |

## Data Notes

- **Cache directory**: `~/.cache/github-report-skill/`
  - `{url_hash}.json` — Raw data cached by URL SHA256 hash
  - `project_index.json` — Cumulative project index across all searches (auto-deduplicated)
- **Category rules**: Can be manually specified, or auto-inferred from Topics → Programming Language → "Uncategorized"
- **Category colors**: 12 built-in color schemes (AI purple, frontend blue, JS gold, Python teal, automation cyan, database pink, etc.). Unmatched categories fall back to default blue.
