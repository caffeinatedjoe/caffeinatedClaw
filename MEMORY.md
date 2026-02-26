# MEMORY.md

## X article to podcast workflow (established)

- For `x.com/.../status/...` links, use the built-in OpenClaw browser profile `openclaw` first.
- Reliable extraction sequence:
  1) open URL,
  2) wait 5-8s,
  3) scroll (`PageDown`) to load article blocks,
  4) evaluate page text and capture the longest relevant block.
- Clean out platform UI noise before narration (trending/sign-up/footer text).
- If body text is inaccessible, check tweet metadata endpoint for article title/preview and state limitations explicitly.
- Convert clean article text to TTS only after confirming body completeness.
- Default audio mode for X articles is verbatim read (unless user asks for summary).
- For long outputs, generate chunked audio only as an intermediate step, then rejoin and export one final compressed MP3 (podcast-friendly) before delivery.
- Name final episode files with a content-relevant slug (e.g., `YYYY-MM-DD-apple-iphone-ai-transcription-tools.mp3`) instead of generic `part` names.
- For all future podcast RSS items, include the original source link in the episode description (`Source: <url>`).
- Apply minimal spoken-word normalization before TTS: replace inline URLs with "source link in description", normalize currency/percent patterns, keep wording otherwise verbatim.
