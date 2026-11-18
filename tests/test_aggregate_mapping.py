import pytest

from safelens.aggregate import map_count_filters


@pytest.mark.parametrize(("text", "category"), [
    ("NMAC conflicts", "Conflict NMAC"),
    ("conflicts NMAC", "Conflict NMAC"),
    ("incursions runway ground", "Ground Incursion Runway"),
    ("runway ground incursion", "Ground Incursion Runway"),
    ("deviations altitude", "Deviation - Altitude Excursion From Assigned Altitude"),
    ("excursions altitude", "Deviation - Altitude Excursion From Assigned Altitude"),
    ("collisions midair near", "Conflict NMAC"),
    ("problems critical equipment", "Aircraft Equipment Problem Critical"),
    ("critical aircraft problem equipment", "Aircraft Equipment Problem Critical"),
])
def test_known_category_token_sets_and_plural_forms(text, category):
    # This is a string mapper test only, never the frozen count question/target.
    assert map_count_filters(text) == {"year_start": None, "year_end": None, "anomaly_category": category}


def test_exact_phrase_priority_and_range_connector():
    assert map_count_filters("Count reports from 2016 to 2018 about runway incursions") == {
        "year_start": 2016, "year_end": 2018, "anomaly_category": "Ground Incursion Runway"}
    assert map_count_filters("Count reports from 2016 to 2018 about assigned altitude excursion deviation from altitude") == {
        "year_start": 2016, "year_end": 2018, "anomaly_category": "Deviation - Altitude Excursion From Assigned Altitude"}


@pytest.mark.parametrize("question", [
    "Count reports about NMAC conflicts from Toronto in 2018",
    "Count reports about runway incursions and NMAC conflicts in 2018",
    "Count reports about equipment problematic critical in 2018",
    "Count reports about nmacrowave in 2018",
    "Count reports in 2016 and 2018 about assigned altitude excursion deviation from altitude",
    "Count reports about assigned altitude excursion deviation froms in 2018",
])
def test_unsupported_qualifiers_ambiguities_and_substrings_still_reject(question):
    assert map_count_filters(question) is None


def test_category_parameter_conflict_still_rejects():
    assert map_count_filters("NMAC conflicts", category="Ground Incursion Runway") is None
