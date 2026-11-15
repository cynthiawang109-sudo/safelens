"""Paragraph-aware source slicing using the embedding model's own tokenizer."""

import bisect
import re


def chunk_report(synopsis, narrative, provider, settings):
    """Return source passages; short reports/final tails may be below 400 tokens.

    Target counts include synopsis and model special tokens. Overlap covers
    narrative tokens; repeating the synopsis is additional context. Prefer a
    paragraph end when it leaves at least 400 total tokens. Oversized paragraphs
    fall back to token windows, preserving source spelling rather than decoding.
    """
    prefix = synopsis + "\n\n" if synopsis else ""
    limit = min(settings.chunk_tokens, provider.max_tokens)
    if provider.count_tokens(prefix) >= limit:
        raise ValueError("Synopsis leaves no narrative token budget; refusing to truncate it")
    offsets = provider.tokenizer(
        narrative, add_special_tokens=False, truncation=False, return_offsets_mapping=True,
    )["offset_mapping"]
    if not offsets:
        raise ValueError("Report has no narrative tokens")
    ends = [end for _, end in offsets]
    boundaries = [bisect.bisect_right(ends, match.start())
                  for match in re.finditer(r"\n\s*\n", narrative)]
    chunks = []
    start = 0
    while start < len(offsets):
        budget = limit - provider.count_tokens(prefix)
        end = min(len(offsets), start + budget)

        def passage(stop, window_start=start):
            return prefix + narrative[offsets[window_start][0]:offsets[stop - 1][1]]

        while end > start and provider.count_tokens(passage(end)) > limit:
            end -= 1
        if end <= start:
            raise ValueError("No narrative token fits alongside synopsis")
        if end < len(offsets):
            for boundary in reversed(boundaries):
                if start < boundary <= end and provider.count_tokens(passage(boundary)) >= 400:
                    end = boundary
                    break
        chunks.append(passage(end))
        if end == len(offsets):
            break
        overlap = round((end - start) * settings.chunk_overlap)
        start = max(start + 1, end - overlap)
    return chunks
