#!/usr/bin/env python3
"""Extract frames from a video; optionally produce GIF and sprite-sheet PNG.

Two invocation styles:
  1. With project: extract-frames.py --action attack [--gif] [--spritesheet]
       Reads gastory-output/<project>/animation/<action>.mp4
       Writes to gastory-output/<project>/frames/<action>/
  2. With explicit path: extract-frames.py path/to/video.mp4 [--gif] ...
       Writes to gastory-output/frames/<basename>/ (legacy layout)

Requires ffmpeg in PATH and Pillow (PIL) for sprite-sheet composition.
"""

import argparse
import math
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gastory import OUTPUT_ROOT, project_subdir, resolve_project  # noqa: E402

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[assignment]


def run(cmd: list[str]) -> None:
    print(f"[gastory] $ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True)


def extract_frames(video: Path, frames_dir: Path, fps: float) -> int:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for f in frames_dir.glob("frame_*.png"):
        f.unlink()
    run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-vf", f"fps={fps}",
            str(frames_dir / "frame_%03d.png"),
        ]
    )
    return len(list(frames_dir.glob("frame_*.png")))


def make_gif(video: Path, gif_path: Path, fps: float, scale: str) -> None:
    palette = gif_path.with_suffix(".palette.png")
    run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-vf", f"fps={fps},scale={scale}:flags=lanczos,palettegen",
            str(palette),
        ]
    )
    run(
        [
            "ffmpeg", "-y",
            "-i", str(video),
            "-i", str(palette),
            "-lavfi",
            f"fps={fps},scale={scale}:flags=lanczos[x];[x][1:v]paletteuse",
            str(gif_path),
        ]
    )
    palette.unlink(missing_ok=True)


def make_spritesheet(frames_dir: Path, sheet_path: Path, cols: int | None) -> tuple[int, int, int]:
    if Image is None:
        raise SystemExit(
            "Pillow가 설치되어 있지 않습니다:\n"
            "  python3 -m pip install --user Pillow"
        )
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        raise SystemExit(f"프레임이 없음: {frames_dir}")
    n = len(frames)
    if cols is None:
        cols = min(8, n)
    rows = math.ceil(n / cols)
    first = Image.open(frames[0])
    fw, fh = first.size
    sheet = Image.new("RGBA", (fw * cols, fh * rows), (0, 0, 0, 0))
    for i, fp in enumerate(frames):
        img = Image.open(fp).convert("RGBA")
        r, c = divmod(i, cols)
        sheet.paste(img, (c * fw, r * fh))
    sheet.save(sheet_path)
    return n, cols, rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="비디오에서 프레임 추출 + 선택적으로 GIF / 스프라이트시트."
    )
    parser.add_argument(
        "video",
        nargs="?",
        default=None,
        help="입력 비디오 파일 경로. --action 사용 시 생략",
    )
    parser.add_argument("--project", default=None, help="프로젝트 이름 (미지정 시 현재 프로젝트)")
    parser.add_argument(
        "--action",
        default=None,
        help="애니메이션 이름. 지정 시 <project>/animation/<action>.mp4 사용",
    )
    parser.add_argument("--fps", type=float, default=10.0)
    parser.add_argument("--gif", action="store_true")
    parser.add_argument("--gif-scale", default="320:-1")
    parser.add_argument("--spritesheet", action="store_true")
    parser.add_argument("--cols", type=int, default=None)
    args = parser.parse_args()

    if args.action:
        project = resolve_project(args.project)
        video_path = OUTPUT_ROOT / project / "animation" / f"{args.action}.mp4"
        if not video_path.is_file():
            raise SystemExit(f"비디오 파일 없음: {video_path}")
        frames_dir = project_subdir(project, "frames", args.action)
        out_root = project_subdir(project, "frames")
        gif_path = out_root / f"{args.action}.gif"
        sheet_path = out_root / f"{args.action}_spritesheet.png"
    elif args.video:
        video_path = Path(args.video).expanduser().resolve()
        if not video_path.is_file():
            raise SystemExit(f"비디오 파일 없음: {video_path}")
        legacy_root = OUTPUT_ROOT / "frames"
        legacy_root.mkdir(parents=True, exist_ok=True)
        frames_dir = legacy_root / video_path.stem
        gif_path = legacy_root / f"{video_path.stem}.gif"
        sheet_path = legacy_root / f"{video_path.stem}_spritesheet.png"
    else:
        parser.error("비디오 파일 경로 또는 --action 중 하나를 지정해주세요.")

    n_frames = extract_frames(video_path, frames_dir, args.fps)
    print(f"[gastory] 프레임 {n_frames}장 → {frames_dir}")

    if args.gif:
        make_gif(video_path, gif_path, args.fps, args.gif_scale)
        print(f"[gastory] GIF: {gif_path}")

    if args.spritesheet:
        n, cols, rows = make_spritesheet(frames_dir, sheet_path, args.cols)
        print(f"[gastory] 스프라이트시트 ({cols}x{rows}, {n} frames): {sheet_path}")


if __name__ == "__main__":
    main()
