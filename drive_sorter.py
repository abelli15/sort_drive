#!/usr/bin/env python3
import argparse
import shutil
from pathlib import Path


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "sort_drive.conf"


def load_config(path: Path) -> dict:
    config = {}
    if not path.is_file():
        return config
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        config[key] = value
    return config


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def iter_media_files(folder: Path):
    return sorted(p for p in folder.iterdir() if p.is_file())


def unique_dest_path(dest_dir: Path, stem: str, suffix: str) -> Path:
    candidate = dest_dir / f"{stem}{suffix}"
    if not candidate.exists():
        return candidate
    i = 2
    while True:
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def main() -> int:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument(
        "--config",
        default=None,
        help="Path to config file (default: sort_drive.conf next to the script).",
    )
    pre_args, _ = pre_parser.parse_known_args()

    config_path = Path(pre_args.config).expanduser() if pre_args.config else DEFAULT_CONFIG_PATH
    config = load_config(config_path)

    dest_default = config.get("DRIVE_SORTER_DEST", "20251200_Fútbol")
    source_root_default = config.get("DRIVE_SORTER_SOURCE_ROOT", "")
    copy_default = parse_bool(config.get("DRIVE_SORTER_COPY", "false"))

    parser = argparse.ArgumentParser(
        description="Moves files from dated folders into one folder and renames them.",
        parents=[pre_parser],
    )
    parser.add_argument(
        "source_folders",
        nargs="*",
        help="One or more source folders that contain files to move/copy.",
    )
    parser.add_argument(
        "--source-root",
        default=source_root_default,
        help="Root folder to take subfolders from (overrides DRIVE_SORTER_SOURCE_ROOT).",
    )
    parser.add_argument(
        "--dest",
        default=dest_default,
        help="Destination folder name/path (overrides DRIVE_SORTER_DEST).",
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        default=copy_default,
        help="Copy files instead of moving them (overrides DRIVE_SORTER_COPY).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without moving files.",
    )
    args = parser.parse_args()

    source_folders = list(args.source_folders)
    if not source_folders and args.source_root:
        root = Path(args.source_root).expanduser().resolve()
        if not root.is_dir():
            raise SystemExit(f"Source root not found or not a directory: {root}")
        source_folders = [str(p) for p in sorted(root.iterdir()) if p.is_dir()]
    if not source_folders:
        raise SystemExit("Provide source folders or --source-root.")

    dest_dir = Path(args.dest).expanduser()
    if not dest_dir.is_absolute():
        dest_dir = (Path.cwd() / dest_dir).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    for folder in sorted(Path(p).expanduser().resolve() for p in source_folders):
        if not folder.is_dir():
            raise SystemExit(f"Source folder not found or not a directory: {folder}")
        if folder.resolve() == dest_dir:
            continue
        index = 1
        for file_path in iter_media_files(folder):
            stem = f"{folder.name}_{index}"
            dest_path = unique_dest_path(dest_dir, stem, file_path.suffix)
            if args.dry_run:
                print(f"DRY RUN: {file_path} -> {dest_path}")
            else:
                if args.copy:
                    shutil.copy2(str(file_path), str(dest_path))
                else:
                    shutil.move(str(file_path), str(dest_path))
            index += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
