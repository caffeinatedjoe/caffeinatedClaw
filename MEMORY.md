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
