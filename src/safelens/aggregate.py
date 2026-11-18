"""Strict metadata count routing: parameterized SQL, never LLM-estimated counts."""

import re

from safelens.subset import CATEGORIES

ALIASES = dict(zip(CATEGORIES, (
    ("runway incursions", "runway incursion", "ground incursion runway"),
    ("altitude deviations", "altitude deviation", "altitude excursions", "altitude excursion"),
    ("near midair collisions", "near midair collision", "nmac", "conflict nmac"),
    ("critical equipment problems", "critical equipment problem", "aircraft equipment problem critical"),
)))


def count_intent(question):
    return bool(re.search(r"\b(how many|number of|count(?: the)?)\b.*\breports?\b", question, re.IGNORECASE))


def category_words(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def map_categories(text):
    """Consume exact phrases first, then known category token sets in any order."""
    phrases = {label: sorted({*aliases, label.lower()}, key=lambda p: (-len(p), p))
               for label, aliases in ALIASES.items()}
    vocabulary = {word for variants in phrases.values() for phrase in variants for word in category_words(phrase)}

    def normalize(word):
        # Only inflections of known category words, not arbitrary stemming.
        return word[:-1] if word.endswith("s") and word[:-1] in vocabulary - {"from"} else word

    words = list(re.finditer(r"[a-z0-9]+", text))
    normalized = [normalize(word.group()) for word in words]
    present = set(normalized)
    removed, categories = set(), []
    for label, variants in phrases.items():
        exact = [match for phrase in variants for match in re.finditer(r"\b" + re.escape(phrase) + r"\b", text)]
        if exact:
            categories.append(label)
            removed.update(word.start() for word in words
                           if any(match.start() <= word.start() and word.end() <= match.end() for match in exact))
        candidates = {frozenset(normalize(word) for word in category_words(phrase)) for phrase in variants}
        matches = sorted((tokens for tokens in candidates if tokens <= present),
                         key=lambda tokens: (-len(tokens), sorted(tokens)))
        if matches:
            if label not in categories:
                categories.append(label)
            consumed = set().union(*matches)
            # A canonical label contains "from". Consume that category word,
            # but preserve an actual "from YEAR" connector for the year grammar.
            removed.update(word.start() for word, normalized_word in zip(words, normalized)
                           if normalized_word in consumed and not (
                               normalized_word == "from" and re.match(r"\s+(?:19|20)\d{2}\b", text[word.end():])))
    remaining = re.sub(r"[a-z0-9]+", lambda match: " " if match.start() in removed else match.group(), text)
    return categories, remaining


def map_count_filters(question, category=None):
    """Only allow a small published count grammar; leftover terms mean unmapped."""
    categories, text = map_categories(question.lower())
    if len(set(categories)) > 1 or (category and categories and category not in categories):
        return None
    selected = categories[0] if categories else category
    years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", text)]
    start = end = None
    if len(years) == 1:
        if re.search(r"\b(since|after|before|until)\b", text):
            if "after" in text:
                start = years[0] + 1
            elif "since" in text:
                start = years[0]
            elif "before" in text:
                end = years[0] - 1
            else:
                end = years[0]
        else:
            start = end = years[0]
    elif len(years) == 2 and re.search(r"\b(between|from)\b", text) and years[0] <= years[1]:
        start, end = years
    elif years:
        return None
    text = re.sub(r"\b(?:19|20)\d{2}\b", " ", text)
    allowed = {"how", "many", "number", "of", "count", "the", "reports", "report", "are", "there", "all", "asrs", "in", "from", "between", "and", "to", "since", "after", "before", "until", "about", "with", "for", "on", "recorded", "submitted", "dataset", "corpus", "total", "a", "an", "were", "was", "during"}
    if any(t not in allowed for t in re.findall(r"[a-z0-9]+", text)):
        return None
    return {"year_start": start, "year_end": end, "anomaly_category": selected}


COUNT_SQL = ("SELECT count(*) FILTER (WHERE (%s::int IS NULL OR report_year >= %s) "
             "AND (%s::int IS NULL OR report_year <= %s) "
             "AND (%s::text IS NULL OR %s=ANY(anomaly_codes))), count(*) FROM reports")


def execute_count(conn, filters):
    start, end, category = (filters[k] for k in ("year_start", "year_end", "anomaly_category"))
    params = [start, start, end, end, category, category]
    count, denominator = conn.execute(COUNT_SQL, params).fetchone()
    return {"count": count, "denominator": denominator, "denominator_definition": "all reports in the active indexed corpus",
            "filters": filters, "sql": COUNT_SQL, "parameters": params,
            "caveat": "Counts of voluntary ASRS reports, not incident rates; metadata labels may overlap and dates have month precision."}
