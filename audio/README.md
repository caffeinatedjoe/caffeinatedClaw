# Episode audio

MP3s are not stored in this tree. They are GitHub Release assets, tagged
`caffeinatedclaw-audio-YYYY` (one release per year).

- Releases: https://github.com/caffeinatedjoe/caffeinatedClaw/releases
- Feed enclosures in `/podcast.xml` must use each asset's
  `browser_download_url` (from `gh release view --json assets`).
- Publish new episodes with `scripts/publish_episode.py` (or
  `~/notebooklm-podcast/publish_to_claw.py` on the Hermes/Chief of Staff box).
- Do not commit `audio/*.mp3`; they are gitignored so the Pages artifact
  stays under GitHub's 1 GB limit.
