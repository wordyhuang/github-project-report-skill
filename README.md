# GitHub Project Report Skill

> **创建时间**：2026-07-06 17:20  
> **最后修改时间**：2026-07-06 17:30  
> **当前版本**：V_1.1  
> **适用对象**：TRAE 平台用户、AI 智能体使用者  
> **核心目标**：为智能体提供 GitHub 项目自动化调研能力 — 给定仓库 URL 自动生成结构化报告，并支持跨项目汇总为可视化列表。  
> **文档简述**：本文档面向智能体的使用者，说明该 skill 是什么、能做什么、怎么安装到你的智能体中。

---

## 目录

- [这是什么技能？](#这是什么技能)
- [技能能力概览](#技能能力概览)
- [文件结构](#文件结构)
- [安装到智能体](#安装到智能体)
- [智能体触发方式](#智能体触发方式)
- [生成的产物](#生成的产物)
- [数据说明](#数据说明)
- [版本变更记录](#版本变更记录)

---

## 这是什么技能？

**GitHub Project Report Skill** 是一个安装到 TRAE 平台的智能体技能。安装后，你的智能体获得了以下能力：

> 只要给它一个 GitHub 仓库链接，它就能自动抓取该项目的元数据、README、配置文件、文档和目录结构，提炼成一份结构化的报告（HTML 或 Markdown）。每次搜索过的项目还会被自动记录下来，你可以随时让智能体生成一张带分类配色、可搜索筛选的可视化卡片列表，方便横向对比和回顾。

简单说：**搜索即归档**。

## 技能能力概览

| 能力 | 说明 |
|------|------|
| **单项目分析** | 给定 GitHub URL，自动采集 Stars/Forks/README/配置文件/docs/目录结构，输出结构化 JSON 和汇总 MD |
| **跨项目汇总列表** | 将所有搜索过的 GitHub 项目汇总为一个自包含 HTML 卡片页面，支持搜索、分类筛选、语言筛选、多种排序 |
| **分类配色** | 按项目分类（AI、前端、后端、自动化等）自动匹配不同色系，每个卡片顶部有对应颜色的色条 |
| **自动追踪** | 每次搜索自动累计到索引中，去重保留最新数据，无需手动管理 |

## 文件结构

```
github-project-report-skill/
├── README.md                ← 本文档（给你看的安装说明）
├── code/
│   ├── SKILL.md             ← 智能体调用指南（告诉智能体怎么用这个技能）
│   ├── github_report.py     ← 项目信息采集器（智能体调用）
│   └── github_list.py       ← 项目汇总列表生成器（智能体调用）
```

## 安装到智能体

### 方法一：一句话安装（推荐）

直接把下面这段提示词发送给你的智能体，它就会自动完成安装：

> 请帮我从 GitHub 仓库 wordyhuang/github-project-report-skill 安装这个 skill。从 code/ 目录下获取 SKILL.md、github_report.py、github_list.py 三个文件，写入到我的项目 .trae/skills/github-project-report-skill/ 目录下。安装完成后确认目录结构是否正确。

发送后，智能体会自动：
1. 从 GitHub 仓库读取三个文件
2. 创建 `.trae/skills/github-project-report-skill/` 目录
3. 将文件写入对应位置
4. 向你确认安装完成

### 方法二：手动复制文件

如果偏好手动操作，该技能已开源到 [wordyhuang/github-project-report-skill](https://github.com/wordyhuang/github-project-report-skill)。将以下三个文件放入 `.trae/skills/github-project-report-skill/` 即可：

| 文件 | 复制到 |
|------|--------|
| `code/SKILL.md` | `.trae/skills/github-project-report-skill/SKILL.md` |
| `code/github_report.py` | `.trae/skills/github-project-report-skill/github_report.py` |
| `code/github_list.py` | `.trae/skills/github-project-report-skill/github_list.py` |

### 安装验证

安装完成后，目录结构应如下所示：

```
你的项目根目录/
├── .trae/
│   └── skills/
│       └── github-project-report-skill/
│           ├── SKILL.md
│           ├── github_report.py
│           └── github_list.py
```

## 智能体触发方式

安装后，当你的智能体接收到以下任一指令时会自动激活该技能：

- 提供了 GitHub 仓库链接，并要求"做简介/报告/教程/入门"
- 要求"分析/提炼/总结某个 GitHub 项目"
- 要求"将 GitHub 项目做成报告/文档"
- 要求"汇总/查看所有搜索过的项目"、"生成项目列表"
- 关键词包含 `github.com` + `报告|简介|教程|入门|分析|总结`

**触发示例**：

```
帮我看一下这个项目：https://github.com/vuejs/core
把我搜索过的 GitHub 项目汇总一下
分析一下 tensorflow/tensorflow 这个仓库
```

## 生成的产物

智能体使用该技能后会生成以下文件：

| 文件 | 说明 |
|------|------|
| `{项目名}-report/collected_data.json` | 单项目的原始采集数据（元数据、README 全文、配置文件等） |
| `{项目名}-report/collected_summary.md` | 单项目的信息汇总 Markdown |
| `github-projects-list.html` | 所有搜索过的项目的可视化卡片列表（带搜索、筛选、排序） |

## 数据说明

- **缓存目录**：`~/.cache/github-report-skill/`
  - `{url_hash}.json` — 按 URL SHA256 哈希缓存的原始数据
  - `project_index.json` — 所有搜索过的项目累计索引（自动去重）
- **分类规则**：可手动指定，也可自动从项目 Topics → 编程语言 → "未分类" 依次推断
- **分类配色**：内置 12 套色系（AI 紫、前端蓝、JS 金、Python 绿、自动化天蓝、数据库粉等），未匹配的分类使用默认蓝色

---

## 版本变更记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| V_1.0 | 2026-07-06 | 初始版本：信息采集 + SKILL.md 定义 |
| V_1.1 | 2026-07-06 | 新增 `github_list.py` 项目汇总列表（分类配色、统一布局、搜索筛选）；`github_report.py` 增加 `--category` / `--no-track` 参数和自动追踪逻辑；更新 SKILL.md |
