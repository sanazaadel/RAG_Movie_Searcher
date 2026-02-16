from pathlib import Path
from typing import List, Optional
import re


# Anything like <i>...</i>, <b class="...">, etc.
HTML_TAG = re.compile(r"<[^>]+>")


SRT_TIMECODE_LINE = re.compile(
    r"^\s*\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}\s*$",
    re.MULTILINE,
)


SRT_INDEX_LINE = re.compile(r"(?m)^\s*\d+\s*$")


def remove_html(text: str) -> str:
    """Strip subtitle styling tags like <i>, <b>, etc."""
    return HTML_TAG.sub("", text or "")


def tidy_spacing(text: str) -> str:
    """
    Remove trailing spaces and collapse multiple newlines to a max of 2.
    trailing spaces are spaces at the end of lines, which can cause issues with formatting and display.
    Multiple newlines can create excessive blank space, so we limit them to two.
    """
    text = re.sub(r"[ \t]+$", "", text or "", flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_srt(
    text: str,
    *,
    remove_tags: bool = True,
    remove_index_lines: bool = False,
    remove_timestamps: bool = False,
) -> str:
    """
    Clean SRT subtitle text based on specified options.
    By default, it removes HTML tags but keeps the SRT structure (timestamps and indices).
     - remove_tags: If True, removes HTML tags like <i>, <b>, etc.
     - remove_index_lines: If True, removes lines that contain only the subtitle index numbers.
     - remove_timestamps: If True, removes lines that contain the SRT timecode format
    """
    out = text or ""

    if remove_tags:
        out = remove_html(out)

    if remove_timestamps:
        out = SRT_TIMECODE_LINE.sub("", out)

    if remove_index_lines:
        out = SRT_INDEX_LINE.sub("", out)

    return tidy_spacing(out)


def srt_to_plain_text(text: str) -> str:
    """
    Convert SRT to plain dialogue text.
    Removes tags, timestamps, and index numbers, then collapses whitespace.
    """
    out = clean_srt(
        text,
        remove_tags=True,
        remove_index_lines=True,
        remove_timestamps=True,
    )
    out = re.sub(r"\s+", " ", out).strip()
    return out


def process_file(
    in_path: Path,
    out_path: Optional[Path] = None,
    *,
    mode: str = "clean_srt",
) -> Path:
    """
    Process a single SRT file based on the specified mode.

    """
    raw = in_path.read_text(encoding="utf-8", errors="ignore")

    if mode == "clean_srt":
        cleaned = clean_srt(
            raw,
            remove_tags=True,
            remove_index_lines=False,
            remove_timestamps=False,
        )
        out_path = out_path or in_path.with_name(in_path.stem + ".clean.srt")
        out_path.write_text(cleaned + "\n", encoding="utf-8")
        return out_path

    if mode == "plain_text":
        txt = srt_to_plain_text(raw)
        out_path = out_path or in_path.with_suffix(".txt")
        out_path.write_text(txt + "\n", encoding="utf-8")
        return out_path

    raise ValueError("Unknown mode: {} (use 'clean_srt' or 'plain_text')".format(mode))


def process_folder(
    folder: Path,
    *,
    mode: str = "clean_srt",
    pattern: str = "*.srt",
) -> List[Path]:
    """Process every matching file in a folder."""
    folder = Path(folder)
    outputs: List[Path] = []

    for p in folder.glob(pattern):
        if p.is_file():
            outputs.append(process_file(p, mode=mode))

    return outputs


