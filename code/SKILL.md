---
name: github-project-report
description: 将任意 GitHub 开源项目提炼为结构化的 HTML 或 Markdown 报告，包含项目介绍、入门教程、使用示例和架构说明。当用户提供 GitHub 仓库链接并要求做简介、报告、教程或分析时触发。
---

# GitHub Project Report Skill

## Identity

将任意 GitHub 开源项目提炼为一份结构化的 HTML 报告。包含项目介绍、核心亮点、技术架构、入门教程、使用示例、流水线/功能一览、配置说明和目录结构。

## Trigger

当用户输入满足以下任一条件时激活：

- 提供了 GitHub 仓库链接，并要求"做简介/报告/教程/入门"
- 要求"分析/提炼/总结某个 GitHub 项目"
- 要求"将 GitHub 项目做成报告/文档"
- 关键词：`github.com` + `报告|简介|教程|入门|分析|总结`

### 格式推断规则

若用户未显式指定格式，按以下规则推断：

| 用户表述 | 推断格式 |
|----------|----------|
| "做成 markdown" / "md 格式" / "给我 markdown" | `md` |
| "导入飞书" / "导入 Notion" / "导入 Lark" | `md` |
| "打印" / "导出文档" / "生成文档" | `md` |
| "做成网页" / "html" / "好看的报告" / "可视化" | `html` |
| 其他默认情况 | `html` |

### 语言推断规则

若用户未显式指定语言，按以下规则推断：

| 用户表述 | 推断语言 |
|----------|----------|
| "英文版" / "in English" / "English version" | `en` |
| 用户使用纯英文查询 | `en` |
| 其他默认情况（含中文查询、混合查询） | `zh` |

## Input

- `github_url`: GitHub 仓库地址（必需）
- `language`: 输出语言（可选，默认 `zh`，可选值：`zh` | `en`）
  - `zh`：报告全部使用中文输出
  - `en`：报告全部使用英文输出
- `format`: 输出格式（可选，默认 `html`，可选值：`html` | `md`）
  - `html`：调用 html-report skill 生成自包含 HTML 文件（精美排版、适合分享）
  - `md`：生成结构化 Markdown 文件（轻量、适合快速浏览、适合导入 Lark/Notion）

## Workflow

### Phase 1: 信息收集

1. **解析仓库地址**
   - 从 URL 提取 `owner` 和 `repo`
   - 兼容带 path/fragment 的 URL，如 `github.com/owner/repo/issues/123`
   - 示例：`https://github.com/calesthio/OpenMontage` → owner=`calesthio`, repo=`OpenMontage`

2. **获取 README**
   - 优先尝试 `README_zh-CN.md`、`README_zh.md`、`README_CN.md`（中文优先）
   - 其次 `README.md`、`readme.md`、`Readme.md`
   - 若 README 超长，基于 H2 章节智能截断，保留前 N 个核心章节
   - 若 README 完全缺失，尝试获取 GitHub 页面渲染内容作为兜底

3. **获取关键源码/配置文件**（并发下载，最多 8 线程）
   - `config.yaml` / `config.json` / `pyproject.toml` / `package.json` — 项目配置
   - `Makefile` — 构建命令与工具脚本
   - `setup.py` / `requirements.txt` / `Cargo.toml` — 依赖与安装信息
   - `Dockerfile` — 部署信息
   - `.env.example` — 环境变量模板
   - `AGENT_GUIDE.md`、`PROJECT_CONTEXT.md`、`ARCHITECTURE.md` — 项目指南
   - 目录结构（通过 GitHub API 获取根目录文件列表）

4. **获取 docs/ 子目录文档**（并发下载）
   - 探测 `docs/` 目录下的 `.md` 文件和关键文档
   - 如 `ARCHITECTURE.md`、`PROVIDERS.md`、`API.md`、`DEPLOYMENT.md` 等

5. **获取仓库元数据**
   - Stars、Forks、License、最近更新时间、主要语言、Topics

#### 失败回退策略

| 失败场景 | 回退动作 |
|----------|----------|
| GitHub API 403 限流 | 提示用户 `--token` 参数，使用 Personal Access Token（5000 次/小时） |
| urllib SSL/超时错误 | 自动回退到 `curl` 命令行工具 |
| README 完全缺失 | 尝试获取 GitHub 页面渲染内容；仍失败则标注"项目未提供 README" |
| 关键文件缺失 | 跳过该文件，继续收集其他文件 |
| 私有仓库无权限 | 提示使用 `--token` 并检查 Token 的 `repo` 权限 |
| 网络完全不可用 | 检查本地缓存，使用缓存数据生成报告 |

#### 缓存机制
- 默认启用本地缓存（`~/.cache/github-report-skill/`）
- 基于 URL SHA256 哈希索引
- 重复分析同一仓库时直接读取缓存，跳过网络请求
- 使用 `--no-cache` 可强制刷新

### Phase 2: 内容提炼

基于收集到的信息，按以下结构提炼内容：

#### 1. 项目介绍
- **一句话定义**：项目是什么、解决什么问题
- **核心差异化**：与同类工具相比的独特价值
- **适用场景**：谁应该使用它、最佳 use case

#### 2. 原文翻译（条件触发）
- 若 README 只有英文且无官方中文文档：
  - 翻译核心章节（Introduction、Quick Start、Features）
  - 保留关键术语原文并附中文解释
- 若已有官方中文文档：直接采用，注明来源

#### 3. 入门教程
- **环境准备**：依赖列表（版本要求、安装命令）
- **安装步骤**：从 clone 到首次运行的完整命令序列
- **首次验证**：如何确认安装成功（如 `make preflight`、hello-world 命令）
- **常用命令速查**：Makefile 主要 target 或 CLI 主要子命令

#### 4. 使用示例
- **零配置/最低配置示例**：不需要额外 API Key 或复杂设置的快速上手
- **典型场景示例**：覆盖项目 3-5 个核心使用场景的完整命令/提示词
- **成本参考**（如项目有公开的成本数据）：附上实际案例和花费

#### 5. 功能/模块一览
- 表格形式列出主要功能模块、产出内容、适用场景
- 标注成熟度（production / beta / alpha）

#### 6. 架构与配置（如源码可读）
- 关键技术架构（分层、状态机、核心组件）
- 关键配置项解释（config 文件核心字段）

#### 7. 项目目录结构
- 仓库根目录树（关键文件夹说明）
- 运行时/输出目录说明（如适用）

### Phase 3: 报告生成

根据 `format` 参数路由到不同的输出管道：

#### 若 `format = html`

1. **调用 html-report skill** 生成自包含 HTML 文件
2. **命名规范**：
   - 目录名：`{repo}-report/` 或直接以项目名命名
   - 主文件名：`{ProjectName}.html`（首字母大写的驼峰或原始项目名）
3. **设计风格**：深色科技风（适合开发者项目）或简洁文档风（适合通用项目）
4. **必须包含的引用来源**：GitHub 仓库主页、README、关键源码文件的原始链接

#### 若 `format = md`

1. **直接生成 Markdown 文件**，无需调用 html-report skill
2. **命名规范**：
   - 文件名：`{ProjectName}.md` 或 `{repo}-report.md`
   - 保存位置：用户 workspace 根目录或 `{repo}-report/` 子目录
3. **内容结构**：与 HTML 版保持一致（项目介绍、亮点、教程、示例、架构、目录结构）
4. **格式要求**：
   - 使用标准 GitHub Flavored Markdown
   - 表格使用 Markdown 原生表格语法
   - 代码块标注语言类型
   - 图片使用相对路径或 GitHub 原始链接
   - 引用来源放在文末 Sources 区块

## Output Specification

### 通用要求

- **语言**：由 `language` 参数控制（`zh` 或 `en`），默认 `zh`
- **文件位置**：用户 workspace 根目录下
- **质量要求**：
  - 代码块使用等宽字体、语法高亮
  - 表格支持横向滚动
  - 移动端适配
  - 关键数据（成本、版本号）使用高亮颜色

### HTML 格式要求

- **文件类型**：自包含 HTML（单文件或含 assets 目录）
- **技术栈**：CSS 变量主题、响应式布局、无外部 CDN 依赖
- **视觉风格**：根据项目类型自动选择（开发者项目 → 深色科技风；通用项目 → 简洁文档风）

### Markdown 格式要求

- **文件类型**：`.md`，标准 GitHub Flavored Markdown
- **文件命名**：`{ProjectName}.md`
- **标题层级**：`#` 封面 → `##` 章节 → `###` 小节 → `####` 子节
- **表格**：原生 Markdown 表格，列数 ≤ 6 列以确保移动端可读
- **代码块**： fenced code blocks 标注语言（如 ```bash、```yaml）
- **引用来源**：文末 `## 参考来源` 区块，使用有序列表 + 超链接
- **图片**：优先使用 GitHub raw 链接，必要时生成本地图片后使用相对路径

### Phase 4: 项目列表生成（可选新增功能）

当用户需要查看所有搜索过的 GitHub 项目汇总时，调用 `github_list.py` 生成自包含 HTML 列表页。

**触发条件**：用户要求"汇总/查看所有搜索过的项目"、"生成项目列表"、"项目收藏"

**功能**：
- 读取 `~/.cache/github-report-skill/project_index.json` 中的累计数据
- 生成包含所有项目的卡片式 HTML 页面
- 支持实时筛选（搜索关键词、分类、编程语言）
- 支持排序（Stars 高低、名称、最近搜索时间）
- 自动适配深色/浅色模式
- 零外部依赖，单文件自包含

**用法**：
```bash
# 生成默认列表
python github_list.py

# 指定输出
python github_list.py -o ./output/my-github-list.html

# 自定义标题
python github_list.py --title "我的 GitHub 收藏"

# 指定默认排序
python github_list.py --sort stars-desc

# 生成后自动打开浏览器
python github_list.py --open
```

**项目分类规则**（优先级从高到低）：
1. 用户通过 `--category` 参数显式指定
2. 项目 Topics 列表的第一个标签
3. 项目主要编程语言
4. "未分类"

**自动追踪**：每次执行 `github_report.py` 都会自动将项目信息追加到累计索引中（去重）。使用 `--no-track` 可跳过追踪。

**数据文件**：
- 累计索引: `~/.cache/github-report-skill/project_index.json`
- 每次搜索后自动更新，按 `full_name` 去重覆盖

## Constraints

- 优先从 README 获取信息；README 不完整时才阅读源码
- 不编造未在仓库中明确声明的功能或数据
- 若某些章节信息不足，明确标注"项目未提供此信息"而非留空
- 翻译时保留技术术语原文（如 pipeline、manifest、checkpoint）
- 不生成超过 3 个 Explore subagent 并行任务
- 脚本层并发线程不超过 8 个，避免对 GitHub 服务器造成压力
- 缓存数据不永久保留，用户可通过 `--no-cache` 强制刷新

## Example Invocation

用户输入：
```
帮我提炼一下这个地址的项目，做一下简介，并做一个简易的教程带我入门：https://github.com/calesthio/OpenMontage
```

执行流程：
1. 解析 URL → owner=calesthio, repo=OpenMontage
2. 获取 README_zh-CN.md（优先）→ 内容完整
3. 获取 config.yaml、Makefile、requirements.txt、AGENT_GUIDE.md、PROJECT_CONTEXT.md
4. 提炼：项目介绍（Agent-first 视频制作）、教程（make setup + 自然语言描述）、示例（零成本/纪录片/AI视觉/电影级）
5. 生成 HTML 报告 → `/workspace/openmontage-report/OpenMontage.html`
6. 自动将项目信息记录到累计索引中（分类自动从 topics 推断）

用户输入（指定分类）：
```
https://github.com/vuejs/core --category "前端框架"
```

用户输入（生成项目列表）：
```
把我搜索过的 GitHub 项目汇总一下
```
