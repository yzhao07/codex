#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


SUPPORTED_EXTENSIONS = {".doc", ".docx"}


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def normalize_visible_text(text: str) -> str:
    return text.rstrip("\r\x07")


def ensure_supported_input(path: Path) -> None:
    if not path.exists():
        fail(f"Input file does not exist: {path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        fail("Input must be a .doc or .docx file.")


def derived_output_path(source: Path) -> Path:
    return source.with_name(f"{source.stem}_grammar_revised.docx")


def run_osascript_file(script_path: Path, *args: str) -> str:
    proc = subprocess.run(
        ["osascript", str(script_path)] + list(args),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or "").strip() or (proc.stdout or "").strip() or "AppleScript failed."
        fail(detail)
    return proc.stdout


def applescript_prepare(source: Path, output: Path) -> dict:
    if output.resolve() == source.resolve():
        fail("Refusing to overwrite the original file.")

    output.parent.mkdir(parents=True, exist_ok=True)
    output.unlink(missing_ok=True)

    script_dir = Path(__file__).resolve().parent
    if source.suffix.lower() == ".docx":
        shutil.copy2(source, output)
    else:
        output.touch()
        run_osascript_file(script_dir / "convert_doc.applescript", str(source), str(output))

    raw = run_osascript_file(script_dir / "extract_segments.applescript", str(output))
    segments = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        segment_index = int(parts[0]) - 1
        start = int(parts[1])
        text = normalize_visible_text(parts[2])
        if not text:
            continue
        segments.append(
            {
                "segment_index": segment_index,
                "start": start,
                "end": start + len(text),
                "text": text,
            }
        )

    return {
        "input_path": str(source),
        "output_path": str(output),
        "segments": segments,
    }


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"Failed to read JSON from {path}: {exc}")


def resolve_span(item: dict, segments_by_index: dict[int, dict]) -> tuple[int, int]:
    segment_index = item.get("segment_index")
    if segment_index is None or segment_index not in segments_by_index:
        fail(f"Unknown segment_index: {segment_index}")

    segment = segments_by_index[segment_index]
    rel_start = item.get("start")
    rel_end = item.get("end")
    if not isinstance(rel_start, int) or not isinstance(rel_end, int):
        fail("Every edit/comment must include integer start and end offsets.")
    if rel_start < 0 or rel_end < rel_start or rel_end > len(segment["text"]):
        fail(f"Invalid span in segment {segment_index}.")

    original = item.get("original")
    if original is not None:
        actual = segment["text"][rel_start:rel_end]
        if actual != original:
            fail(
                f"Original text mismatch for segment {segment_index}: "
                f"expected {original!r}, found {actual!r}."
            )

    return segment["start"] + rel_start, segment["start"] + rel_end


def build_apply_payload(document: Path, plan: dict) -> dict:
    prepared = plan.get("prepared_document")
    if prepared and Path(prepared).resolve() != document.resolve():
        fail("Plan prepared_document does not match the target document.")

    segments = plan.get("segments")
    if not isinstance(segments, list):
        fail("Plan must include the segments array from prepare.")

    segments_by_index = {}
    for segment in segments:
        idx = segment.get("segment_index")
        if not isinstance(idx, int):
            fail("Each segment must include an integer segment_index.")
        segments_by_index[idx] = segment

    edits = []
    for item in plan.get("edits", []):
        abs_start, abs_end = resolve_span(item, segments_by_index)
        replacement = item.get("replacement")
        if replacement is None:
            fail("Each edit must include replacement.")
        edits.append(
            {
                "abs_start": abs_start,
                "abs_end": abs_end,
                "replacement_text": replacement,
            }
        )

    comments = []
    for item in plan.get("comments", []):
        abs_start, abs_end = resolve_span(item, segments_by_index)
        comment_text = item.get("comment")
        if not comment_text:
            fail("Each comment must include comment text.")
        comments.append(
            {
                "abs_start": abs_start,
                "abs_end": abs_end,
                "comment_text": comment_text,
            }
        )

    edits.sort(key=lambda item: item["abs_start"], reverse=True)
    previous_start = None
    for edit in edits:
        if previous_start is not None and edit["abs_end"] > previous_start:
            fail("Edit spans overlap.")
        previous_start = edit["abs_start"]

    return {
        "document_path": str(document),
        "comments": comments,
        "edits": edits,
    }


def applescript_apply(document: Path, payload: dict) -> None:
    script_dir = Path(__file__).resolve().parent
    run_osascript_file(script_dir / "apply_review.applescript", str(document), json.dumps(payload))


def cmd_prepare(args: argparse.Namespace) -> None:
    source = Path(args.input_path).expanduser().resolve()
    ensure_supported_input(source)
    output = derived_output_path(source)
    result = applescript_prepare(source, output)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_apply(args: argparse.Namespace) -> None:
    document = Path(args.document).expanduser().resolve()
    if document.suffix.lower() != ".docx":
        fail("Apply requires a .docx target document.")
    if not document.exists():
        fail(f"Target document does not exist: {document}")

    plan = load_json(Path(args.plan).expanduser().resolve())
    payload = build_apply_payload(document, plan)
    applescript_apply(document, payload)
    print(str(document))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prepare and apply tracked grammar reviews in Microsoft Word.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("input_path")
    prepare_parser.set_defaults(func=cmd_prepare)

    apply_parser = subparsers.add_parser("apply")
    apply_parser.add_argument("--document", required=True)
    apply_parser.add_argument("--plan", required=True)
    apply_parser.set_defaults(func=cmd_apply)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
