#!/usr/bin/env python3
"""Publish an MP3 episode into caffeinatedjoe/caffeinatedClaw.

Uploads the file to the year's GitHub Release (creates
`caffeinatedclaw-audio-YYYY` if needed), then inserts a podcast.xml item
whose enclosure uses the release asset URL — never a Pages /audio/ path.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape


REPO = "caffeinatedjoe/caffeinatedClaw"
FEED_BASE = "https://joecoffey.me/caffeinatedClaw"
PAGES_FEED = "https://caffeinatedjoe.github.io/caffeinatedClaw"


def run_gh(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], check=check, capture_output=True, text=True)


def run_gh_json(args: list[str]) -> dict:
    return json.loads(run_gh(args).stdout)


def get_file(path: str) -> tuple[str, str]:
    data = run_gh_json(["api", f"repos/{REPO}/contents/{path}"])
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def put_file(path: str, content: bytes | str, message: str, sha: str | None = None) -> None:
    content_b = content.encode("utf-8") if isinstance(content, str) else content
    body: dict = {
        "message": message,
        "content": base64.b64encode(content_b).decode("ascii"),
        "branch": "main",
    }
    if sha:
        body["sha"] = sha
    proc = subprocess.run(
        ["gh", "api", "-X", "PUT", f"repos/{REPO}/contents/{path}", "--input", "-"],
        input=json.dumps(body),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)


def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s[:60] or "episode"


def duration_hms(seconds: float) -> str:
    secs = int(round(seconds))
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def probe_duration(mp3: Path) -> float:
    try:
        out = subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(mp3),
            ],
            text=True,
        ).strip()
        return float(out)
    except Exception:
        return 0.0


def insert_item(xml: str, item_xml: str) -> str:
    m = re.search(r"<item>", xml)
    if m:
        return xml[: m.start()] + item_xml + "\n" + xml[m.start() :]
    return xml.replace("</channel>", item_xml + "\n  </channel>")


def release_tag(year: int) -> str:
    return f"caffeinatedclaw-audio-{year}"


def ensure_year_release(year: int) -> str:
    tag = release_tag(year)
    view = run_gh(["release", "view", tag, "-R", REPO], check=False)
    if view.returncode == 0:
        return tag
    notes = (
        f"Episode MP3s for Hermes Signal / caffeinatedClaw ({year}), "
        "stored as GitHub Release assets so the GitHub Pages artifact "
        "stays under the 1 GB limit.\n\n"
        f"Podcast feed: {FEED_BASE}/podcast.xml"
    )
    run_gh(
        [
            "release",
            "create",
            tag,
            "-R",
            REPO,
            "--title",
            f"caffeinatedClaw episode audio ({year})",
            "--notes",
            notes,
            "--target",
            "main",
        ]
    )
    return tag


def asset_url_from_release(tag: str, name: str) -> str | None:
    data = run_gh_json(["release", "view", tag, "-R", REPO, "--json", "assets"])
    for a in data.get("assets") or []:
        if a.get("name") == name:
            # gh exposes the browser download URL as "url"
            return a.get("url") or a.get("browserDownloadUrl") or a.get("browser_download_url")
    return None


def upload_to_year_release(mp3: Path, asset_name: str, year: int) -> str:
    """Upload mp3 to caffeinatedclaw-audio-YYYY and return its browser download URL."""
    tag = ensure_year_release(year)
    existing = asset_url_from_release(tag, asset_name)
    if existing:
        # Re-upload if a same-named asset is a different file.
        data = run_gh_json(["release", "view", tag, "-R", REPO, "--json", "assets"])
        size = next(a["size"] for a in data["assets"] if a["name"] == asset_name)
        if size == mp3.stat().st_size:
            return existing
        run_gh(["release", "upload", tag, str(mp3), "-R", REPO, "--clobber"])
    else:
        # Upload with the intended name (source path may differ).
        staged = mp3
        if mp3.name != asset_name:
            staged = mp3.with_name(asset_name)
            raise RuntimeError(
                f"Refusing to rename {mp3.name} to {asset_name} in place; "
                "pass an --mp3 whose filename already matches the asset name."
            )
        run_gh(["release", "upload", tag, str(staged), "-R", REPO])
    url = asset_url_from_release(tag, asset_name)
    if not url:
        raise RuntimeError(f"Uploaded {asset_name} to {tag} but could not read its asset URL")
    return url


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mp3", required=True, type=Path)
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--source-url", default="")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    # Never publish stamp titles like "NotebookLM episode 20260928T220527Z" — require a clear human title.
    if re.match(r"(?i)^NotebookLM\s+episode\s+\d{8}T\d{6}Z$", args.title.strip()) or not args.title.strip():
        print(
            f"Refusing stamp/empty title {args.title!r}. Pass a clear human --title "
            "(page title, NotebookLM audio artifact title, or caller override).",
            file=sys.stderr,
        )
        return 2

    if not args.mp3.is_file():
        print(f"MP3 not found: {args.mp3}", file=sys.stderr)
        return 1

    date = datetime.now(timezone.utc)
    date_slug = date.strftime("%Y-%m-%d")
    slug = f"{date_slug}-{slugify(args.title)}"
    asset_name = f"{slug}.mp3"
    size = args.mp3.stat().st_size
    duration = duration_hms(probe_duration(args.mp3))
    guid = f"caffeinatedclaw-{slug}-{uuid.uuid4().hex[:8]}"

    desc = args.description.strip()
    if args.source_url:
        desc = (desc + f" Source: {args.source_url}").strip()
    if not desc:
        desc = f"NotebookLM Audio Overview. Source: {args.source_url or 'n/a'}"

    print(f"Episode: {args.title}")
    print(f"Asset name: {asset_name}")
    print(f"Size: {size} bytes, duration: {duration}")

    if args.dry_run:
        tag = release_tag(date.year)
        audio_url = f"https://github.com/{REPO}/releases/download/{tag}/{asset_name}"
        print(f"(dry-run) would upload to {tag} and use enclosure {audio_url}")
        return 0

    # Copy to a temp name if the source filename doesn't match the asset name.
    upload_path = args.mp3
    tmp = None
    if args.mp3.name != asset_name:
        tmp = Path("/tmp") / asset_name
        tmp.write_bytes(args.mp3.read_bytes())
        upload_path = tmp
    try:
        audio_url = upload_to_year_release(upload_path, asset_name, date.year)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()

    item = f"""    <item>
      <title>{escape(args.title)}</title>
      <description>{escape(desc)}</description>
      <pubDate>{format_datetime(date)}</pubDate>
      <guid isPermaLink="false">{escape(guid)}</guid>
      <enclosure url="{escape(audio_url)}" length="{size}" type="audio/mpeg"/>
      <itunes:author>Hermes</itunes:author>
      <itunes:duration>{duration}</itunes:duration>
      <itunes:explicit>false</itunes:explicit>
    </item>
"""

    xml, xml_sha = get_file("podcast.xml")
    new_xml = insert_item(xml, item)
    put_file("podcast.xml", new_xml, f"Publish episode: {args.title}", sha=xml_sha)

    print(f"Enclosure: {audio_url}")
    print("Published to caffeinatedClaw (audio on GitHub Releases, not Pages).")
    print(f"Feed: {FEED_BASE}/podcast.xml")
    print(f"Also: {PAGES_FEED}/podcast.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
