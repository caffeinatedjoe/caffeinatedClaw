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

## Output rules

- Default to verbatim reading when user asks for article-to-podcast conversion (no summary unless requested).
- If full text is incomplete, say so clearly before generating audio.
- For podcast audio:
  - Keep original wording intact.
  - Remove only platform UI/nav/engagement noise.
  - Preserve key steps/lists from the article.

## Long-audio handling (required)

1. If TTS text is too long for one pass, synthesize in sequential chunks (part1, part2, ...).
2. Rejoin chunks at the end into one master file.
3. Export compressed podcast format as MP3 (single file), default 96 kbps mono.
4. Deliver the combined MP3 as the primary output (parts are intermediate artifacts).
