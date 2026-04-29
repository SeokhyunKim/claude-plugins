"""Shared helpers for gastory scripts: env-file loading, API key resolution,
project state, slug generation, and image encoding.
"""

import base64
import os
import re
import sys
from pathlib import Path


OUTPUT_ROOT = Path("./gastory-output")
STATE_FILE = OUTPUT_ROOT / ".current"


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse a minimal KEY=VALUE .env file. Ignores comments and blank lines."""
    env: dict[str, str] = {}
    if not path.is_file():
        return env
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def resolve_api_key(env_key: str) -> str:
    """Find an API key by checking env var, then ~/.config/gastory/.env, then ./.env."""
    if key := os.environ.get(env_key):
        return key
    home_env = Path.home() / ".config" / "gastory" / ".env"
    if key := parse_env_file(home_env).get(env_key):
        return key
    cwd_env = Path.cwd() / ".env"
    if key := parse_env_file(cwd_env).get(env_key):
        return key
    raise SystemExit(
        f"{env_key}를 찾을 수 없습니다. 다음 중 하나에 설정해주세요:\n"
        f"  1. 환경변수: export {env_key}=...\n"
        f"  2. {home_env} (권장)\n"
        f"  3. {cwd_env}"
    )


def resolve_project(cli_project: str | None) -> str:
    """Resolve current project name. Priority: --project CLI > GASTORY_PROJECT env > .current file."""
    if cli_project:
        return cli_project
    if env_p := os.environ.get("GASTORY_PROJECT"):
        return env_p
    if STATE_FILE.is_file():
        name = STATE_FILE.read_text(encoding="utf-8").strip()
        if name:
            return name
    raise SystemExit(
        "현재 프로젝트가 설정되지 않았습니다. 다음 중 하나로 지정해주세요:\n"
        "  1. /gastory:project <name>으로 현재 프로젝트 설정 (이후 자동 사용)\n"
        "  2. --project <name> 플래그 직접 전달\n"
        "  3. GASTORY_PROJECT 환경변수 설정"
    )


def project_subdir(project: str, *parts: str) -> Path:
    """Return (and create) a subdirectory under gastory-output/<project>/."""
    p = OUTPUT_ROOT / project
    for part in parts:
        p = p / part
    p.mkdir(parents=True, exist_ok=True)
    return p


def slugify(text: str, max_len: int = 40) -> str:
    """Lowercase URL-safe slug; preserves Unicode letters."""
    s = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:max_len] or "untitled"


def image_to_data_uri(image_path: Path) -> str:
    """Read a local image file and return a base64 data URI."""
    data = image_path.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        mime = "image/png"
    elif data[:2] == b"\xff\xd8":
        mime = "image/jpeg"
    elif data[:6] in (b"GIF87a", b"GIF89a"):
        mime = "image/gif"
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        raise SystemExit(f"지원하지 않는 이미지 포맷: {image_path}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
