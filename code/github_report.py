#!/usr/bin/env python3
"""
GitHub Project Report Skill — 自动化信息收集器（增强版）

用法:
    python github_report.py <github_url> [选项]

示例:
    python github_report.py https://github.com/calesthio/OpenMontage
    python github_report.py https://github.com/calesthio/OpenMontage --token ghp_xxx
    python github_report.py https://github.com/calesthio/OpenMontage -v --max-readme-chapters 10
    python github_report.py https://github.com/calesthio/OpenMontage --language en --format md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# ========== 配置 ==========
README_CANDIDATES = [
    "README_zh-CN.md",
    "README_zh.md",
    "README_CN.md",
    "README.md",
    "readme.md",
    "Readme.md",
]

KEY_FILES = [
    "config.yaml",
    "config.json",
    "pyproject.toml",
    "package.json",
    "Makefile",
    "setup.py",
    "requirements.txt",
    "Cargo.toml",
    "go.mod",
    "Dockerfile",
    ".env.example",
    "AGENT_GUIDE.md",
    "PROJECT_CONTEXT.md",
    "ARCHITECTURE.md",
    "CONTRIBUTING.md",
    "LICENSE",
]

DOCS_KEY_FILES = [
    "ARCHITECTURE.md",
    "PROVIDERS.md",
    "API.md",
    "DEPLOYMENT.md",
    "DESIGN.md",
    "TROUBLESHOOTING.md",
]

GITHUB_API_BASE = "https://api.github.com/repos"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

CACHE_DIR = Path.home() / ".cache" / "github-report-skill"


# ========== 国际化 ==========
_I18N = {
    "zh": {
        "debug": "调试",
        "warn": "警告",
        "error": "错误",
        "rate_limit": "GitHub API 请求频率超限。请使用 --token 传入 Personal Access Token 以提高限额。",
        "parse_url_fail": "无法解析 GitHub URL: {url}",
        "collecting": "[→] 正在收集 {owner}/{repo} 的信息...",
        "step_meta": "  [{idx}/5] 获取仓库元数据...",
        "step_readme": "  [{idx}/5] 获取 README...",
        "found_readme": "      ✓ 找到 {filename} ({chars} 字符, {chapters} 个章节)",
        "no_readme": "      ✗ 未找到 README",
        "step_keyfiles": "  [{idx}/5] 获取关键配置文件...",
        "found_keyfiles": "      ✓ 找到 {count} 个文件: {files}",
        "no_keyfiles": "      ✗ 未找到关键配置文件",
        "step_docs": "  [{idx}/5] 获取 docs/ 文档...",
        "found_docs": "      ✓ 找到 {count} 个 docs 文件: {files}",
        "no_docs": "      ✗ 未找到 docs/ 文档",
        "step_dir": "  [{idx}/5] 获取目录结构...",
        "found_dir": "      ✓ 根目录共 {count} 项",
        "saved_json": "[✓] JSON 数据: {path}",
        "saved_md": "[✓] Markdown 汇总: {path}",
        "done": "[✓] 信息收集完成。数据保存在: {dir}/",
        "hint_html": "    格式偏好: HTML。接下来可调用 html-report skill 生成精美报告。",
        "hint_md": "    格式偏好: Markdown。接下来可直接生成 Markdown 报告。",
        "hint_default": "    接下来可以使用这些数据生成 HTML 或 Markdown 报告。",
        "dir_label": "目录",
        "file_label": "文件",
        "summary_title": "信息收集汇总",
        "summary_repo": "仓库",
        "summary_stars": "Stars",
        "summary_forks": "Forks",
        "summary_license": "License",
        "summary_lang": "Language",
        "summary_branch": "Default Branch",
        "section_readme": "README",
        "section_docs": "docs/ 文档",
        "section_keyfiles": "关键配置文件",
        "section_dir": "目录结构",
    },
    "en": {
        "debug": "DEBUG",
        "warn": "WARN",
        "error": "ERROR",
        "rate_limit": "GitHub API rate limit exceeded. Use --token with a Personal Access Token to increase the quota.",
        "parse_url_fail": "Unable to parse GitHub URL: {url}",
        "collecting": "[→] Collecting info for {owner}/{repo}...",
        "step_meta": "  [{idx}/5] Fetching repository metadata...",
        "step_readme": "  [{idx}/5] Fetching README...",
        "found_readme": "      ✓ Found {filename} ({chars} chars, {chapters} chapters)",
        "no_readme": "      ✗ README not found",
        "step_keyfiles": "  [{idx}/5] Fetching key config files...",
        "found_keyfiles": "      ✓ Found {count} files: {files}",
        "no_keyfiles": "      ✗ No key config files found",
        "step_docs": "  [{idx}/5] Fetching docs/ documents...",
        "found_docs": "      ✓ Found {count} docs files: {files}",
        "no_docs": "      ✗ No docs/ documents found",
        "step_dir": "  [{idx}/5] Fetching directory structure...",
        "found_dir": "      ✓ Root directory has {count} items",
        "saved_json": "[✓] JSON data: {path}",
        "saved_md": "[✓] Markdown summary: {path}",
        "done": "[✓] Collection complete. Data saved to: {dir}/",
        "hint_html": "    Format preference: HTML. Next, call html-report skill to generate a polished report.",
        "hint_md": "    Format preference: Markdown. Next, generate a Markdown report directly.",
        "hint_default": "    Next, use this data to generate an HTML or Markdown report.",
        "dir_label": "DIR",
        "file_label": "FILE",
        "summary_title": "Information Collection Summary",
        "summary_repo": "Repository",
        "summary_stars": "Stars",
        "summary_forks": "Forks",
        "summary_license": "License",
        "summary_lang": "Language",
        "summary_branch": "Default Branch",
        "section_readme": "README",
        "section_docs": "docs/ Documents",
        "section_keyfiles": "Key Config Files",
        "section_dir": "Directory Structure",
    },
}


def _T(key: str, lang: str = "zh", **kwargs) -> str:
    """获取国际化文本。"""
    text = _I18N.get(lang, _I18N["zh"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text


# ========== 日志工具 ==========
class Logger:
    def __init__(self, verbose: bool = False, quiet: bool = False, lang: str = "zh"):
        self.verbose = verbose
        self.quiet = quiet
        self.lang = lang

    def debug(self, msg: str) -> None:
        if self.verbose and not self.quiet:
            print(f"[{_T('debug', self.lang)}] {msg}")

    def info(self, msg: str) -> None:
        if not self.quiet:
            print(msg)

    def warn(self, msg: str) -> None:
        if not self.quiet:
            print(f"[{_T('warn', self.lang)}] {msg}", file=sys.stderr)

    def error(self, msg: str) -> None:
        if not self.quiet:
            print(f"[{_T('error', self.lang)}] {msg}", file=sys.stderr)


# ========== 缓存工具 ==========
def cache_path(url: str) -> Path:
    h = hashlib.sha256(url.encode()).hexdigest()[:16]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{h}.json"


def load_cache(url: str) -> str | None:
    cp = cache_path(url)
    if cp.exists():
        try:
            data = json.loads(cp.read_text(encoding="utf-8"))
            return data.get("content")
        except Exception:
            pass
    return None


def save_cache(url: str, content: str, etag: str | None = None) -> None:
    cp = cache_path(url)
    try:
        cp.write_text(
            json.dumps({"url": url, "etag": etag, "content": content}, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


# ========== 网络工具 ==========
def fetch_text(url: str, timeout: int = 15, token: str | None = None, use_cache: bool = True, logger: Logger | None = None) -> tuple[str | None, str | None]:
    """获取 URL 的文本内容。返回 (内容, 错误提示)。"""
    log = logger or Logger()

    # 缓存命中
    if use_cache:
        cached = load_cache(url)
        if cached is not None:
            log.debug(f"cache hit: {url}")
            return cached, None

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHub-Report-Skill/2.0)",
        "Accept": "text/plain, text/html, application/json",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    # 尝试 urllib
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                content = resp.read().decode("utf-8", errors="replace")
                etag = resp.headers.get("ETag")
                if use_cache:
                    save_cache(url, content, etag)
                return content, None
    except urllib.error.HTTPError as e:
        if e.code == 403:
            return None, _T("rate_limit", log.lang)
        if e.code == 404:
            return None, None  # 静默 404
        log.debug(f"urllib HTTPError {e.code} for {url}")
    except Exception as e:
        log.debug(f"urllib error for {url}: {e}")

    # 回退到 curl
    try:
        cmd = ["curl", "-sL", "--max-time", str(timeout)]
        if token:
            cmd.extend(["-H", f"Authorization: token {token}"])
        cmd.append(url)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )
        if result.returncode == 0 and result.stdout:
            if use_cache:
                save_cache(url, result.stdout)
            return result.stdout, None
    except Exception as e:
        log.debug(f"curl error for {url}: {e}")

    return None, None


def fetch_json(url: str, timeout: int = 15, token: str | None = None, use_cache: bool = True, logger: Logger | None = None) -> dict[str, Any] | None:
    text, err = fetch_text(url, timeout, token, use_cache, logger)
    if err:
        return {"__error": err}
    if text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
    return None


# ========== 解析工具 ==========
def parse_github_url(url: str) -> tuple[str, str]:
    """从 GitHub URL 提取 owner 和 repo，兼容带 path/fragment 的 URL。"""
    patterns = [
        r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/|$|#)",
        r"github\.com/([^/]+)/([^/]+?)/?\?",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1), match.group(2)
    raise ValueError(f"无法解析 GitHub URL: {url}")


# ========== 数据获取 ==========
def find_readme(owner: str, repo: str, branch: str, token: str | None, use_cache: bool, logger: Logger) -> tuple[str, str] | None:
    """尝试多个 README 文件名，返回 (文件名, 内容)。"""
    for name in README_CANDIDATES:
        url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{name}"
        content, err = fetch_text(url, token=token, use_cache=use_cache, logger=logger)
        if err:
            logger.warn(err)
        if content:
            return name, content
    return None


def fetch_single_file(url: str, filename: str, token: str | None, use_cache: bool, logger: Logger) -> tuple[str, str] | None:
    """获取单个文件，返回 (文件名, 内容)。"""
    content, err = fetch_text(url, token=token, use_cache=use_cache, logger=logger)
    if err:
        logger.warn(err)
    if content:
        return filename, content
    return None


def fetch_key_files(owner: str, repo: str, branch: str, token: str | None, use_cache: bool, logger: Logger) -> dict[str, str]:
    """并发获取关键配置文件。"""
    results: dict[str, str] = {}
    urls = [(f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{fn}", fn) for fn in KEY_FILES]

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(fetch_single_file, url, fn, token, use_cache, logger): fn
            for url, fn in urls
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                results[res[0]] = res[1]

    return results


def fetch_docs_files(owner: str, repo: str, branch: str, token: str | None, use_cache: bool, logger: Logger) -> dict[str, str]:
    """获取 docs/ 子目录下的关键文档。"""
    results: dict[str, str] = {}

    # 先获取 docs/ 目录内容
    docs_api_url = f"{GITHUB_API_BASE}/{owner}/{repo}/contents/docs?ref={branch}"
    docs_list = fetch_json(docs_api_url, token=token, use_cache=use_cache, logger=logger)
    if not docs_list or not isinstance(docs_list, list):
        return results

    # 构建要获取的文件列表
    docs_files = []
    for item in docs_list:
        if item.get("type") != "file":
            continue
        name = item.get("name", "")
        if name.endswith(".md") or name in DOCS_KEY_FILES:
            docs_files.append(name)

    # 并发获取
    urls = [(f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/docs/{fn}", f"docs/{fn}") for fn in docs_files]
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(fetch_single_file, url, fn, token, use_cache, logger): fn
            for url, fn in urls
        }
        for future in as_completed(futures):
            res = future.result()
            if res:
                results[res[0]] = res[1]

    return results


def fetch_repo_metadata(owner: str, repo: str, token: str | None, use_cache: bool, logger: Logger) -> dict[str, Any]:
    """获取仓库元数据。"""
    url = f"{GITHUB_API_BASE}/{owner}/{repo}"
    data = fetch_json(url, token=token, use_cache=use_cache, logger=logger)
    if data is None:
        return {}
    if isinstance(data, dict) and "__error" in data:
        logger.error(data["__error"])
        return {}

    return {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "language": data.get("language"),
        "license": data.get("license", {}).get("name") if data.get("license") else None,
        "default_branch": data.get("default_branch", "main"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "topics": data.get("topics", []),
        "html_url": data.get("html_url"),
    }


def fetch_directory_structure(owner: str, repo: str, branch: str, token: str | None, use_cache: bool, logger: Logger) -> list[dict[str, Any]]:
    """获取仓库根目录的文件列表。"""
    url = f"{GITHUB_API_BASE}/{owner}/{repo}/contents?ref={branch}"
    data = fetch_json(url, token=token, use_cache=use_cache, logger=logger)
    if isinstance(data, dict) and "__error" in data:
        logger.error(data["__error"])
        return []
    if isinstance(data, list):
        return [
            {
                "name": item.get("name"),
                "type": item.get("type"),
                "path": item.get("path"),
                "html_url": item.get("html_url"),
            }
            for item in data
        ]
    return []


# ========== 内容处理 ==========
def truncate_readme_by_chapters(content: str, max_chapters: int = 20) -> str:
    """基于 Markdown H2 章节智能截断 README，保留前 N 个章节。"""
    if not content:
        return content

    # 匹配 ## 开头的章节
    chapter_pattern = re.compile(r"^(##\s+.+)$", re.MULTILINE)
    matches = list(chapter_pattern.finditer(content))

    if len(matches) <= max_chapters:
        return content

    # 保留到第 N 个章节开头之前的内容
    cutoff = matches[max_chapters].start()
    truncated = content[:cutoff].rstrip()
    return truncated + f"\n\n... ({len(matches) - max_chapters} more chapters truncated)"


# ========== 输出保存 ==========
# ========== 项目索引追踪 ==========
TRACKING_FILE = CACHE_DIR / "project_index.json"


def load_project_index() -> list[dict[str, Any]]:
    """加载累计项目追踪索引。"""
    if TRACKING_FILE.exists():
        try:
            data = json.loads(TRACKING_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else data.get("projects", [])
        except Exception:
            pass
    return []


def save_project_index(projects: list[dict[str, Any]]) -> None:
    """保存累计项目追踪索引。"""
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRACKING_FILE.write_text(
        json.dumps({"version": "1.0", "count": len(projects), "projects": projects}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def track_project(metadata: dict[str, Any], category: str | None, lang: str, logger: Logger) -> None:
    """将当前项目追加到项目追踪索引中（去重，按 full_name 覆盖）。"""
    if not metadata.get("full_name"):
        return

    entry = {
        "name": metadata.get("name"),
        "full_name": metadata.get("full_name"),
        "description": metadata.get("description"),
        "stars": metadata.get("stars", 0),
        "forks": metadata.get("forks", 0),
        "language": metadata.get("language"),
        "topics": metadata.get("topics", []),
        "category": category or _auto_category(metadata),
        "url": metadata.get("html_url", f"https://github.com/{metadata.get('full_name', '')}"),
        "searched_at": __import__("datetime").datetime.now().isoformat(),
    }

    projects = load_project_index()
    # 去重：按 full_name 覆盖
    existing = {p.get("full_name"): i for i, p in enumerate(projects)}
    if entry["full_name"] in existing:
        projects[existing[entry["full_name"]]] = entry
    else:
        projects.append(entry)

    save_project_index(projects)
    logger.debug(f"tracked project: {entry['full_name']} (total: {len(projects)})")


def _auto_category(metadata: dict[str, Any]) -> str:
    """自动推断项目分类：优先 topics，其次 language，最后 '未分类'。"""
    topics = metadata.get("topics", [])
    if topics:
        return topics[0]
    lang = metadata.get("language")
    if lang:
        return lang
    return "未分类"


def save_collected_data(
    output_dir: Path,
    owner: str,
    repo: str,
    metadata: dict[str, Any],
    readme: tuple[str, str] | None,
    key_files: dict[str, str],
    docs_files: dict[str, str],
    directory: list[dict[str, Any]],
    max_readme_chapters: int,
    format_pref: str,
    lang: str,
    logger: Logger,
) -> None:
    """将收集到的数据保存为 JSON 和 Markdown。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存原始数据 JSON
    raw_data = {
        "repo": f"{owner}/{repo}",
        "language_preference": lang,
        "format_preference": format_pref,
        "metadata": metadata,
        "readme": {"filename": readme[0], "content": readme[1]} if readme else None,
        "key_files": key_files,
        "docs_files": docs_files,
        "directory": directory,
    }
    json_path = output_dir / "collected_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    logger.info(_T("saved_json", lang, path=json_path))

    # 保存汇总 Markdown
    md_path = output_dir / "collected_summary.md"
    lines: list[str] = []
    lines.append(f"# {metadata.get('name', repo)} — {_T('summary_title', lang)}")
    lines.append("")
    lines.append(f"- **{_T('summary_repo', lang)}**: {metadata.get('html_url', f'https://github.com/{owner}/{repo}')}")
    lines.append(f"- **{_T('summary_stars', lang)}**: {metadata.get('stars', 'N/A')} | **{_T('summary_forks', lang)}**: {metadata.get('forks', 'N/A')}")
    lines.append(f"- **{_T('summary_license', lang)}**: {metadata.get('license', 'N/A')} | **{_T('summary_lang', lang)}**: {metadata.get('language', 'N/A')}")
    lines.append(f"- **{_T('summary_branch', lang)}**: {metadata.get('default_branch', 'main')}")
    lines.append("")

    if metadata.get("description"):
        lines.append(f"> {metadata['description']}")
        lines.append("")

    if readme:
        lines.append(f"## {_T('section_readme', lang)} ({readme[0]})")
        lines.append("")
        lines.append("```markdown")
        content = truncate_readme_by_chapters(readme[1], max_readme_chapters)
        lines.append(content)
        lines.append("```")
        lines.append("")

    if docs_files:
        lines.append(f"## {_T('section_docs', lang)}")
        lines.append("")
        for fname in sorted(docs_files.keys()):
            fcontent = docs_files[fname]
            lines.append(f"### {fname}")
            lines.append("```markdown")
            lines.append(truncate_readme_by_chapters(fcontent, 5))
            lines.append("```")
            lines.append("")

    if key_files:
        lines.append(f"## {_T('section_keyfiles', lang)}")
        lines.append("")
        for fname in sorted(key_files.keys()):
            fcontent = key_files[fname]
            lines.append(f"### {fname}")
            lines.append("```")
            lines.append(fcontent[:5000])
            if len(fcontent) > 5000:
                lines.append("... (truncated)")
            lines.append("```")
            lines.append("")

    if directory:
        lines.append(f"## {_T('section_dir', lang)}")
        lines.append("")
        for item in directory:
            icon = f"[{_T('dir_label', lang)}]" if item.get("type") == "dir" else f"[{_T('file_label', lang)}]"
            lines.append(f"- {icon} `{item['name']}`")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info(_T("saved_md", lang, path=md_path))


# ========== 主函数 ==========
def main() -> int:
    parser = argparse.ArgumentParser(
        description="GitHub Project Report Skill — 自动化信息收集器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python github_report.py https://github.com/owner/repo
  python github_report.py https://github.com/owner/repo --token ghp_xxx
  python github_report.py https://github.com/owner/repo -v --max-readme-chapters 15
  python github_report.py https://github.com/owner/repo --format md
  python github_report.py https://github.com/owner/repo --format html --token ghp_xxx
  python github_report.py https://github.com/owner/repo --language en --format md
""",
    )
    parser.add_argument("url", help="GitHub 仓库地址")
    parser.add_argument("--output-dir", "-o", default=None, help="输出目录（默认: ./{repo}-report）")
    parser.add_argument("--token", "-t", default=None, help="GitHub Personal Access Token（用于私有仓库和避免 API 限流）")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细调试信息")
    parser.add_argument("--quiet", "-q", action="store_true", help="仅显示错误信息")
    parser.add_argument("--no-cache", action="store_true", help="禁用本地缓存")
    parser.add_argument("--max-readme-chapters", type=int, default=20, help="README 保留的最大章节数（默认 20）")
    parser.add_argument("--format", "-f", choices=["html", "md", "json"], default="json", help="输出格式偏好（默认 json，记录到元数据中供后续生成报告使用）")
    parser.add_argument("--language", "-l", choices=["zh", "en"], default="zh", help="输出语言（默认 zh，可选 zh/en）")
    parser.add_argument("--category", "-c", default=None, help="项目分类标签（用于项目索引，默认自动从 topics/language 推断）")
    parser.add_argument("--no-track", action="store_true", help="不将本此搜索记录到项目索引中")
    args = parser.parse_args()

    logger = Logger(verbose=args.verbose, quiet=args.quiet, lang=args.language)
    use_cache = not args.no_cache
    lang = args.language

    try:
        owner, repo = parse_github_url(args.url)
    except ValueError as e:
        logger.error(_T("parse_url_fail", lang, url=args.url))
        return 1

    logger.info(_T("collecting", lang, owner=owner, repo=repo))

    # 1. 元数据
    logger.info(_T("step_meta", lang, idx=1))
    metadata = fetch_repo_metadata(owner, repo, args.token, use_cache, logger)
    branch = metadata.get("default_branch", "main")
    logger.debug(f"      default_branch={branch}")

    # 2. README
    logger.info(_T("step_readme", lang, idx=2))
    readme = find_readme(owner, repo, branch, args.token, use_cache, logger)
    if readme:
        chapters = len(re.findall(r"^##\s+.+$", readme[1], re.MULTILINE))
        logger.info(_T("found_readme", lang, filename=readme[0], chars=len(readme[1]), chapters=chapters))
    else:
        logger.warn(_T("no_readme", lang))

    # 3. 关键文件（并发）
    logger.info(_T("step_keyfiles", lang, idx=3))
    key_files = fetch_key_files(owner, repo, branch, args.token, use_cache, logger)
    if key_files:
        logger.info(_T("found_keyfiles", lang, count=len(key_files), files=", ".join(sorted(key_files.keys()))))
    else:
        logger.warn(_T("no_keyfiles", lang))

    # 4. docs/ 文档（并发）
    logger.info(_T("step_docs", lang, idx=4))
    docs_files = fetch_docs_files(owner, repo, branch, args.token, use_cache, logger)
    if docs_files:
        logger.info(_T("found_docs", lang, count=len(docs_files), files=", ".join(sorted(docs_files.keys()))))
    else:
        logger.debug(_T("no_docs", lang))

    # 5. 目录结构
    logger.info(_T("step_dir", lang, idx=5))
    directory = fetch_directory_structure(owner, repo, branch, args.token, use_cache, logger)
    logger.info(_T("found_dir", lang, count=len(directory)))

    # 保存
    output_dir = Path(args.output_dir) if args.output_dir else Path(f"{repo}-report")
    save_collected_data(
        output_dir, owner, repo, metadata, readme,
        key_files, docs_files, directory,
        args.max_readme_chapters, args.format, lang, logger,
    )

    # 记录到项目索引
    if not args.no_track:
        track_project(metadata, args.category, lang, logger)

    logger.info(_T("done", lang, dir=output_dir))
    if args.format == "html":
        logger.info(_T("hint_html", lang))
    elif args.format == "md":
        logger.info(_T("hint_md", lang))
    else:
        logger.info(_T("hint_default", lang))
    return 0


if __name__ == "__main__":
    sys.exit(main())
