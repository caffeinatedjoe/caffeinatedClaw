#!/usr/bin/env python3
"""Rebuild genesis/podcast.xml: a pointer-only audio feed for Cornerstone Bible
Church's "Genesis" sermon series on Subsplash.

Reads the same public data the Subsplash series page loads in the browser. The
page hands every anonymous visitor a short-lived guest token; this script reads
it from the page at run time, keeps it in memory only, and never writes or
prints it. No audio is copied: enclosures point at the church's CDN files.
Video-only items are skipped. Output is deterministic, so re-running with no
upstream changes leaves the file byte-identical.

Usage: python3 genesis/build_feed.py   (writes podcast.xml next to this file)
"""
import json, re, sys, urllib.request
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

PAGE = "https://subsplash.com/u/cornerstonebiblechur/media/l/hnnz7xb-genesis"
SERIES_URL = "https://cornerstonebiblechur.subspla.sh/hnnz7xb"
SERIES_ID = "5b273c10-83b0-411b-97f7-bbcb9c2a1f36"
BASE = "https://joecoffey.me/caffeinatedClaw/genesis"
OUT = Path(__file__).resolve().parent / "podcast.xml"
UA = {"User-Agent": "Mozilla/5.0 (caffeinatedClaw genesis feed builder)"}


def get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def guest_auth():
    m = re.search(r'\\"guest\\":\\"(eyJ[\w.-]+)', get(PAGE))
    if not m:
        sys.exit("Could not find the page's guest token; Subsplash page layout changed.")
    return {"Authorization": "Bearer " + m.group(1)}


def fetch_items(auth):
    items, page = [], 1
    while True:
        url = ("https://core.subsplash.com/media/v1/media-items"
               f"?filter%5Bmedia_series%5D={SERIES_ID}&filter%5Bstatus%5D=published"
               f"&page%5Bsize%5D=100&page%5Bnumber%5D={page}&sort=position"
               "&include=audio,audio.audio-outputs,video")
        d = json.loads(get(url, auth))
        batch = d.get("_embedded", {}).get("media-items", [])
        items += batch
        if len(items) >= d.get("total", 0) or not batch:
            return items
        page += 1


def hms(ms):
    s = round(ms / 1000)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}"


def build(items):
    items = sorted(items, key=lambda i: (i["date"], i["position"]))
    eps, skipped = [], []
    for i in items:
        outs = ((i.get("_embedded", {}).get("audio") or {}).get("_embedded", {}).get("audio-outputs") or [])
        if not outs:
            skipped.append(i)
            continue
        eps.append((i, outs[0]))

    xml_items = []
    for n, (i, a) in enumerate(eps, 1):
        d = datetime.strptime(i["date"][:10], "%Y-%m-%d")
        # The date Subsplash shows, pinned to 18:00 UTC so it reads as the same day in US time zones.
        pub = d.strftime("%a, %d %b %Y 18:00:00 +0000")
        link = f"https://subspla.sh/{i['short_code']}"
        scripture = i.get("subtitle") or ""
        speaker = i.get("speaker") or "Cornerstone Bible Church"
        desc = " | ".join(x for x in [scripture, speaker, d.strftime("%B %-d, %Y")] if x)
        desc += f"\n\nCornerstone Bible Church, Albany, OR. Sermon page: {link}"
        url = a["_links"]["related"]["href"]
        xml_items.append(f"""    <item>
      <title>{escape(i['title'])}</title>
      <description>{escape(desc)}</description>
      <link>{escape(link)}</link>
      <guid isPermaLink="false">subsplash-{i['id']}</guid>
      <pubDate>{pub}</pubDate>
      <enclosure url="{escape(url)}" length="{a.get('file_size', 0)}" type="audio/mpeg"/>
      <itunes:title>{escape(i['title'])}</itunes:title>
      <itunes:author>{escape(speaker)}</itunes:author>
      <itunes:subtitle>{escape(scripture)}</itunes:subtitle>
      <itunes:summary>{escape(desc)}</itunes:summary>
      <itunes:duration>{hms(a.get('duration', 0))}</itunes:duration>
      <itunes:episode>{n}</itunes:episode>
      <itunes:episodeType>full</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>
    </item>""")

    channel = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
     xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Genesis – Cornerstone Bible Church</title>
    <link>{SERIES_URL}</link>
    <language>en-us</language>
    <description>Genesis: How It All Begins. Sermon series from Cornerstone Bible Church, Albany, OR, in series order. Audio streams from the church's own Subsplash files. Series page: {SERIES_URL}</description>
    <atom:link href="{BASE}/podcast.xml" rel="self" type="application/rss+xml"/>
    <itunes:author>Cornerstone Bible Church</itunes:author>
    <itunes:summary>Genesis: How It All Begins, a sermon series from Cornerstone Bible Church, Albany, OR.</itunes:summary>
    <itunes:type>serial</itunes:type>
    <itunes:block>Yes</itunes:block>
    <itunes:explicit>false</itunes:explicit>
    <itunes:category text="Religion &amp; Spirituality"><itunes:category text="Christianity"/></itunes:category>
    <itunes:image href="{BASE}/cover.jpg"/>
    <image>
      <url>{BASE}/cover.jpg</url>
      <title>Genesis – Cornerstone Bible Church</title>
      <link>{SERIES_URL}</link>
    </image>
{chr(10).join(xml_items)}
  </channel>
</rss>
"""
    return channel, eps, skipped


def main():
    channel, eps, skipped = build(fetch_items(guest_auth()))
    old = OUT.read_text() if OUT.exists() else None
    if old != channel:
        OUT.write_text(channel)
    print(f"episodes={len(eps)} skipped_video_only={len(skipped)} changed={old != channel}")
    for i in skipped:
        print(f"  skipped (no audio): {i['date'][:10]} {i['title']} https://subspla.sh/{i['short_code']}")
    if eps:
        f, l = eps[0][0], eps[-1][0]
        print(f"  first: {f['date'][:10]} {f['title']}\n  last:  {l['date'][:10]} {l['title']}")


if __name__ == "__main__":
    main()
