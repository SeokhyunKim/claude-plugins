#!/usr/bin/env python3
"""Manage current project state in ./gastory-output/.current.

Usage:
    project.py                  # show current project
    project.py <name>           # set current project (creates dir if needed)
    project.py --clear          # clear current project
    project.py --list           # list known projects (subdirs of gastory-output/)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _gastory import OUTPUT_ROOT, STATE_FILE  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="현재 작업 중인 gastory 프로젝트를 관리합니다."
    )
    parser.add_argument("name", nargs="?", help="설정할 프로젝트 이름")
    parser.add_argument("--clear", action="store_true", help="현재 프로젝트 해제")
    parser.add_argument("--list", action="store_true", help="알려진 프로젝트 목록 출력")
    args = parser.parse_args()

    if args.list:
        if not OUTPUT_ROOT.is_dir():
            print(f"{OUTPUT_ROOT} 디렉토리가 없습니다.")
            return
        projects = sorted(
            d.name for d in OUTPUT_ROOT.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )
        if not projects:
            print(f"{OUTPUT_ROOT}에 프로젝트가 없습니다.")
            return
        current = STATE_FILE.read_text(encoding="utf-8").strip() if STATE_FILE.is_file() else None
        for p in projects:
            marker = " ← current" if p == current else ""
            print(f"  {p}{marker}")
        return

    if args.clear:
        if STATE_FILE.exists():
            STATE_FILE.unlink()
            print("현재 프로젝트를 해제했습니다.")
        else:
            print("설정된 현재 프로젝트가 없습니다.")
        return

    if args.name is None:
        if STATE_FILE.is_file():
            current = STATE_FILE.read_text(encoding="utf-8").strip()
            project_dir = OUTPUT_ROOT / current
            print(f"현재 프로젝트: {current}")
            print(f"디렉토리: {project_dir.resolve()}")
        else:
            print("현재 프로젝트가 설정되지 않았습니다. /gastory:project <name>으로 설정하세요.")
            sys.exit(1)
        return

    project_dir = OUTPUT_ROOT / args.name
    project_dir.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(args.name + "\n", encoding="utf-8")
    print(f"현재 프로젝트: {args.name}")
    print(f"디렉토리: {project_dir.resolve()}")


if __name__ == "__main__":
    main()
