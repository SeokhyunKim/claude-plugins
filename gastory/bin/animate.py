#!/usr/bin/env python3
"""Image-to-video via fal.ai Seedance 2.0 or xAI grok-imagine-video.

Output: gastory-output/<project>/animation/<action>.mp4 + .json sidecar.
Default input image: most recent PNG in gastory-output/<project>/concept/, or specified by --source.
"""

import argparse
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
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
    "fal-seedance": {
        "env_key": "FAL_KEY",
        "default_model": "bytedance/seedance-2.0/fast/image-to-video",
    },
    "xai": {
        "env_key": "XAI_API_KEY",
        "default_model": "grok-imagine-video",
    },
}

DEFAULT_PROVIDER = "fal-seedance"
POLL_INTERVAL_SEC = 3
POLL_TIMEOUT_SEC = 600

CAMERA_LOCK_SUFFIX = (
    "카메라는 완전히 고정되어 있고 줌인/줌아웃이나 이동이 전혀 없다. "
    "케릭터의 위치와 크기, 화면 내 차지하는 비율, 시선 방향, 전체 실루엣을 그대로 유지한다. "
    "static camera, no camera movement, no zoom, fixed framing, "
    "character size and position constant in frame."
)


def find_source_image(project: str, source: str | None, image_path: str | None) -> Path:
    """Resolve which still image to animate."""
    if image_path:
        p = Path(image_path).expanduser()
        if not p.is_file():
            raise SystemExit(f"이미지 파일 없음: {p}")
        return p
    concept_dir = OUTPUT_ROOT / project / "concept"
    if source:
        p = concept_dir / f"{source}.png"
        if not p.is_file():
            raise SystemExit(
                f"--source {source} 에 해당하는 파일을 찾을 수 없음: {p}\n"
                f"사용 가능한 이름: {[f.stem for f in concept_dir.glob('*.png')]}"
            )
        return p
    if not concept_dir.is_dir():
        raise SystemExit(
            f"프로젝트 '{project}'에 concept 디렉토리가 없습니다: {concept_dir}\n"
            "먼저 /gastory:concept-art로 원화를 생성하세요."
        )
    pngs = sorted(concept_dir.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not pngs:
        raise SystemExit(
            f"프로젝트 '{project}'의 concept 디렉토리에 PNG가 없습니다: {concept_dir}"
        )
    return pngs[0]


def http_request(method: str, url: str, headers: dict, body: dict | None = None,
                 timeout: int = 300) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"{method} {url}\nAPI 오류 (HTTP {e.code}):\n{detail}")
    except urllib.error.URLError as e:
        raise SystemExit(f"네트워크 오류: {e.reason}")


def http_download(url: str, dest: Path, timeout: int = 600) -> None:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        dest.write_bytes(r.read())


def call_fal_seedance(args, api_key: str, image_data_uri: str) -> tuple[str, dict]:
    submit_url = f"https://queue.fal.run/{args.model}"
    auth = {"Authorization": f"Key {api_key}"}
    body = {
        "image_url": image_data_uri,
        "prompt": args.prompt,
        "duration": str(args.duration),
        "resolution": args.resolution,
        "generate_audio": args.audio,
    }
    print("[gastory] fal.ai 제출 중...", file=sys.stderr)
    submit = http_request(
        "POST", submit_url, {**auth, "Content-Type": "application/json"}, body
    )
    request_id = submit.get("request_id")
    status_url = submit.get("status_url")
    response_url = submit.get("response_url")
    if not (request_id and status_url and response_url):
        raise SystemExit(f"예상치 못한 응답: {json.dumps(submit)[:500]}")
    print(f"[gastory] 큐 등록. request_id={request_id}", file=sys.stderr)

    deadline = time.time() + POLL_TIMEOUT_SEC
    last_status = None
    while time.time() < deadline:
        st = http_request("GET", status_url, auth)
        status = st.get("status")
        if status != last_status:
            print(f"[gastory] status={status}", file=sys.stderr)
            last_status = status
        if status == "COMPLETED":
            result = http_request("GET", response_url, auth)
            video_url = result.get("video", {}).get("url")
            if not video_url:
                raise SystemExit(f"video.url 없음: {json.dumps(result)[:500]}")
            return video_url, result
        if status in ("FAILED", "CANCELLED"):
            raise SystemExit(f"생성 실패 (status={status}): {json.dumps(st)[:500]}")
        time.sleep(POLL_INTERVAL_SEC)
    raise SystemExit(f"타임아웃: {POLL_TIMEOUT_SEC}초 내 완료되지 않음")


def call_xai(args, api_key: str, image_data_uri: str) -> tuple[str, dict]:
    submit_url = "https://api.x.ai/v1/videos/generations"
    auth = {"Authorization": f"Bearer {api_key}"}
    body: dict = {
        "model": args.model,
        "prompt": args.prompt,
        "image": image_data_uri,
        "duration": args.duration,
        "resolution": args.resolution,
    }
    if args.aspect_ratio:
        body["aspect_ratio"] = args.aspect_ratio

    print("[gastory] xAI 제출 중...", file=sys.stderr)
    submit = http_request(
        "POST", submit_url, {**auth, "Content-Type": "application/json"}, body
    )
    request_id = submit.get("request_id")
    if not request_id:
        raise SystemExit(f"예상치 못한 응답: {json.dumps(submit)[:500]}")
    print(f"[gastory] 큐 등록. request_id={request_id}", file=sys.stderr)

    poll_url = f"https://api.x.ai/v1/videos/{request_id}"
    deadline = time.time() + POLL_TIMEOUT_SEC
    last_status = None
    while time.time() < deadline:
        st = http_request("GET", poll_url, auth)
        status = st.get("status")
        if status != last_status:
            print(f"[gastory] status={status}", file=sys.stderr)
            last_status = status
        if status == "done":
            video_url = st.get("video", {}).get("url")
            if not video_url:
                raise SystemExit(f"video.url 없음: {json.dumps(st)[:500]}")
            return video_url, st
        if status in ("expired", "failed"):
            raise SystemExit(f"생성 실패 (status={status}): {json.dumps(st)[:500]}")
        time.sleep(POLL_INTERVAL_SEC)
    raise SystemExit(f"타임아웃: {POLL_TIMEOUT_SEC}초 내 완료되지 않음")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="이미지 → 비디오 (fal.ai Seedance 2.0 / xAI grok-imagine-video)."
    )
    parser.add_argument("prompt", help="동작 설명 프롬프트")
    parser.add_argument("--project", default=None, help="프로젝트 이름 (미지정 시 현재 프로젝트)")
    parser.add_argument(
        "--source",
        default=None,
        help='입력 이미지 이름 (concept 디렉토리 내). 미지정 시 가장 최근 PNG 사용',
    )
    parser.add_argument(
        "--action",
        default=None,
        help='애니메이션 이름 (예: attack, idle, walk). 미지정 시 프롬프트에서 자동 생성',
    )
    parser.add_argument(
        "--image",
        default=None,
        help="입력 이미지 경로 직접 지정 (--project, --source 무시)",
    )
    parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        default=DEFAULT_PROVIDER,
    )
    parser.add_argument("--model", default=None)
    parser.add_argument(
        "--duration", type=int, default=5, help="비디오 길이 (초). 기본: 5"
    )
    parser.add_argument(
        "--resolution", default="720p", choices=["480p", "720p"]
    )
    parser.add_argument(
        "--aspect-ratio",
        default=None,
        help="[xai 전용] 1:1, 16:9, 9:16 등. 미지정 시 입력 이미지 비율 사용",
    )
    parser.add_argument(
        "--audio",
        action="store_true",
        help="[fal-seedance] 오디오 생성 활성화 (기본: 끔). 게임 에셋엔 보통 불필요",
    )
    parser.add_argument(
        "--free-camera",
        action="store_true",
        help="기본 카메라/구도 고정 지시문을 프롬프트에 추가하지 않음 (시네마틱/컷씬용)",
    )
    args = parser.parse_args()

    user_prompt = args.prompt
    if not args.free_camera:
        args.prompt = f"{args.prompt} {CAMERA_LOCK_SUFFIX}"

    project = resolve_project(args.project)
    image_path = find_source_image(project, args.source, args.image)
    action = args.action or slugify(user_prompt)

    cfg = PROVIDERS[args.provider]
    if args.model is None:
        args.model = cfg["default_model"]
    api_key = resolve_api_key(cfg["env_key"])

    image_data_uri = image_to_data_uri(image_path)

    print(
        f"[gastory] project={project} action={action} source={image_path.name}\n"
        f"[gastory] 생성 중... provider={args.provider} model={args.model} "
        f"duration={args.duration}s resolution={args.resolution}",
        file=sys.stderr,
    )

    if args.provider == "fal-seedance":
        video_url, raw_result = call_fal_seedance(args, api_key, image_data_uri)
    else:
        video_url, raw_result = call_xai(args, api_key, image_data_uri)

    anim_dir = project_subdir(project, "animation")
    video_path = anim_dir / f"{action}.mp4"
    meta_path = anim_dir / f"{action}.json"

    if video_path.exists():
        print(f"[gastory] 경고: 기존 비디오 덮어씀: {video_path}", file=sys.stderr)

    print(f"[gastory] 비디오 다운로드 중...", file=sys.stderr)
    http_download(video_url, video_path)

    metadata = {
        "project": project,
        "action": action,
        "user_prompt": user_prompt,
        "prompt": args.prompt,
        "camera_lock_applied": not args.free_camera,
        "provider": args.provider,
        "model": args.model,
        "duration": args.duration,
        "resolution": args.resolution,
        "aspect_ratio": args.aspect_ratio,
        "audio": args.audio,
        "input_image": str(image_path.resolve()),
        "video_url": video_url,
        "video_path": str(video_path.resolve()),
        "created_at": datetime.datetime.now().isoformat(),
    }
    meta_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"[gastory] 비디오: {video_path}")
    print(f"[gastory] 메타데이터: {meta_path}")


if __name__ == "__main__":
    main()
