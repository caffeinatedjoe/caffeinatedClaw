---
name: x-article-podcast
description: Extract full long-form X articles from x.com links (especially /status/ links that point to /i/article/) and prepare text for podcast narration. Use when a user sends an X link and asks to summarize, narrate, or convert it to audio.
---

# x-article-podcast

Use this workflow for reliable extraction.

## Primary path (OpenClaw built-in browser)

1. Open link with browser profile `openclaw`.
2. Wait 5-8 seconds.
3. Scroll once or twice (`PageDown`) to trigger lazy content.
4. Extract content via evaluate from `document.body.innerText` and article/tweet containers.
5. Keep the longest useful text block and strip UI boilerplate like:
   - "See new posts"
   - "Trending now"
   - "Sign up"
   - footer/legal blocks
6. If extracted text contains article body paragraphs, proceed to summary or TTS.

## Fallback path (when browser extraction fails)

1. Try tweet metadata endpoint:
   - `https://cdn.syndication.twimg.com/tweet-result?id=<tweet_id>&token=x`
2. If an `article.rest_id` is present but body is unavailable, report that login/session access is required.
3. If Chrome relay is requested, ensure tab is attached and retry extraction.

## Output mode rules

- Default mode: verbatim reading when user asks for article-to-podcast conversion.
- If user asks for a “podcast version” / conversational adaptation, use Podcastfy mode.
- If full text is incomplete, say so clearly before generating audio.

### Verbatim mode
- Keep original wording intact.
- Remove only platform UI/nav/engagement noise.
- Preserve key steps/lists from the article.

### Podcastfy mode
- Generate a conversational two-speaker transcript (minimum necessary rewriting for flow).
- Keep factual fidelity to the source article.
- Produce audio via Podcastfy (Edge TTS when API keys are unavailable).
- Label episode title/description as `podcastfy edition`.

## Spoken-word normalization (minimal-edit, required)

Before TTS, run a listening pass with minimal edits:

- Keep meaning and sequence unchanged.
- Replace inline URLs with `[source link in description]`.
- Convert obvious TTS-unfriendly tokens:
  - `$2,000-$5,000` -> `2,000 to 5,000 dollars`
  - `$297/month` -> `297 dollars per month`
  - `84%` -> `84 percent`
  - `1)` -> `1.`
- Do not rewrite paragraph content into summaries.

Use script:
- `skills/x-article-podcast/scripts/normalize_for_tts.py`
- Input: raw cleaned article text on stdin
- Output: TTS-ready spoken text on stdout

## Voice default (required)

- Default local voice: `vits-piper-en_US-hfc_male-medium` (hfc_male).
- Use this as the standard voice unless the user explicitly asks for a different voice.

## Long-audio handling (required)

1. If TTS text is too long for one pass, synthesize in sequential chunks (part1, part2, ...).
2. Rejoin chunks at the end into one master file.
3. Export compressed podcast format as MP3 (single file), default 96 kbps mono.
4. Deliver the combined MP3 as the primary output (parts are intermediate artifacts).

## Episode filename convention (required)

Use content-relevant slugs instead of generic names.

Pattern:
- `YYYY-MM-DD-<topic-slug>.mp3`

Slug rules:
- Derive from article headline/topic (not author name alone).
- Lowercase letters, numbers, hyphens only.
- Remove stopwords when possible; keep 4-8 meaningful tokens.
- Keep under ~80 chars.

Examples:
- `2026-02-26-apple-iphone-ai-transcription-tools.mp3`
- `2026-03-01-openai-agents-enterprise-adoption.mp3`

## RSS description/source attribution (required)

For every new episode item in `podcast.xml`:
- Include the original source URL in `<description>`.
- Format: short summary line + `Source: <url>`.
- Use the exact link the user sent (or canonical X status URL if cleaned).
