#!/usr/bin/env python3
"""Generate concept art via OpenAI gpt-image-2 or xAI grok-imagine-image.

Output: gastory-output/<project>/concept/<name>.png + .json sidecar
"""

import argparse
import base64
import datetime
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gastory import (  # noqa: E402
    OUTPUT_ROOT,
    image_to_data_uri,
    project_subdir,
    resolve_api_key,
    resolve_project,
    slugify,
)


PROVIDERS = {
    "openai": {
        "env_key": "OPENAI_API_KEY",
        "endpoint": "https://api.openai.com/v1/images/generations",
        "edit_endpoint": "https://api.openai.com/v1/images/edits",
        "default_model": "gpt-image-2",
    },
    "xai": {
        "env_key": "XAI_API_KEY",
        "endpoint": "https://api.x.ai/v1/images/generations",
        "edit_endpoint": "https://api.x.ai/v1/images/edits",
        "default_model": "grok-imagine-image",
    },
}

DEFAULT_PROVIDER = "openai"


def build_request_body(provider: str, args: argparse.Namespace) -> dict:
    body: dict = {"model": args.model, "prompt": args.prompt, "n": 1}
    if provider == "openai":
        body["size"] = args.size
    elif provider == "xai":
        body["aspect_ratio"] = args.aspect_ratio
        body["resolution"] = args.resolution
        body["response_format"] = "b64_json"
    return body


def post_json(url: str, body: dict, api_key: str) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API 오류 (HTTP {e.code}):\n{detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"네트워크 오류: {e.reason}")


def extract_image_bytes(data: dict) -> bytes:
    item = data.get("data", [{}])[0]
    if b64 := item.get("b64_json"):
        return base64.b64decode(b64)
    if url := item.get("url"):
        with urllib.request.urlopen(url, timeout=120) as r:
            return r.read()
    raise SystemExit(f"예상치 못한 응답 형식: {json.dumps(data)[:500]}")


def call_generate(provider: str, body: dict, api_key: str) -> bytes:
    endpoint = PROVIDERS[provider]["endpoint"]
    return extract_image_bytes(post_json(endpoint, body, api_key))


def call_xai_edit(prompt: str, model: str, image_data_uri: str, api_key: str) -> bytes:
    endpoint = PROVIDERS["xai"]["edit_endpoint"]
    body = {
        "model": model,
        "prompt": prompt,
        "image": {"url": image_data_uri, "type": "image_url"},
        "response_format": "b64_json",
    }
    return extract_image_bytes(post_json(endpoint, body, api_key))


def _build_multipart(fields: dict[str, str], image_path: Path) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(f"--{boundary}\r\n".encode())
        chunks.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        chunks.append(value.encode("utf-8"))
        chunks.append(b"\r\n")
    chunks.append(f"--{boundary}\r\n".encode())
    chunks.append(
        f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'.encode()
    )
    chunks.append(b"Content-Type: image/png\r\n\r\n")
    chunks.append(image_path.read_bytes())
    chunks.append(b"\r\n")
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def call_openai_edit(
    prompt: str, model: str, image_path: Path, api_key: str, size: str
) -> bytes:
    endpoint = PROVIDERS["openai"]["edit_endpoint"]
    body, content_type = _build_multipart(
        {"model": model, "prompt": prompt, "n": "1", "size": size}, image_path
    )
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": content_type,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"API 오류 (HTTP {e.code}):\n{detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"네트워크 오류: {e.reason}")
    return extract_image_bytes(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenAI 또는 xAI 이미지 모델로 게임 에셋 원화를 생성합니다."
    )
    parser.add_argument("prompt", help="이미지 생성 프롬프트")
    parser.add_argument("--project", default=None, help="프로젝트 이름 (미지정 시 현재 프로젝트 사용)")
    parser.add_argument(
        "--name",
        default=None,
        help='에셋 이름 (예: "main", "background"). 미지정 시 프롬프트에서 자동 생성',
    )
    parser.add_argument(
        "--from",
        dest="from_name",
        default=None,
        help="참고 이미지 이름 (현재 프로젝트의 concept 디렉토리). 지정 시 image-to-image edit으로 동작",
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        default=DEFAULT_PROVIDER,
    )
    parser.add_argument("--model", default=None, help="모델 이름. 미지정 시 provider 기본값")
    parser.add_argument(
        "--size", default="1024x1024", help="[openai 전용] 예: 1024x1024, 1536x1024"
    )
    parser.add_argument(
        "--aspect-ratio", default="1:1", help="[xai 전용] 예: 1:1, 16:9, 9:16"
    )
    parser.add_argument(
        "--resolution", default="1k", choices=["1k", "2k"], help="[xai 전용]"
    )
    args = parser.parse_args()

    project = resolve_project(args.project)
    name = args.name or slugify(args.prompt)

    cfg = PROVIDERS[args.provider]
    if args.model is None:
        args.model = cfg["default_model"]
    api_key = resolve_api_key(cfg["env_key"])

    concept_dir = project_subdir(project, "concept")
    png_path = concept_dir / f"{name}.png"
    meta_path = concept_dir / f"{name}.json"

    if png_path.exists():
        print(f"[gastory] 경고: 기존 파일 덮어씀: {png_path}", file=sys.stderr)

    if args.from_name:
        ref_path = OUTPUT_ROOT / project / "concept" / f"{args.from_name}.png"
        if not ref_path.is_file():
            available = sorted(p.stem for p in (OUTPUT_ROOT / project / "concept").glob("*.png"))
            raise SystemExit(
                f"참고 이미지 없음: {ref_path}\n"
                f"사용 가능한 이름: {available or '(없음)'}"
            )
        print(
            f"[gastory] image-to-image 생성 중... project={project} name={name} "
            f"from={args.from_name} provider={args.provider} model={args.model}",
            file=sys.stderr,
        )
        if args.provider == "openai":
            image_bytes = call_openai_edit(
                args.prompt, args.model, ref_path, api_key, args.size
            )
        else:
            image_bytes = call_xai_edit(
                args.prompt, args.model, image_to_data_uri(ref_path), api_key
            )
        request_body_meta = {"mode": "edit", "from": args.from_name}
    else:
        print(
            f"[gastory] 생성 중... project={project} name={name} "
            f"provider={args.provider} model={args.model}",
            file=sys.stderr,
        )
        body = build_request_body(args.provider, args)
        image_bytes = call_generate(args.provider, body, api_key)
        request_body_meta = {k: v for k, v in body.items() if k != "prompt"}

    png_path.write_bytes(image_bytes)

    metadata = {
        "project": project,
        "name": name,
        "prompt": args.prompt,
        "provider": args.provider,
        "model": args.model,
        "request_body": request_body_meta,
        "created_at": datetime.datetime.now().isoformat(),
        "image_path": str(png_path.resolve()),
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[gastory] 이미지: {png_path}")
    print(f"[gastory] 메타데이터: {meta_path}")


if __name__ == "__main__":
    main()
