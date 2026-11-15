from dataclasses import replace

import pytest

from safelens.config import Settings
from safelens.ingest import normalize


@pytest.fixture
def raw():
    return {
        "acn_num_ACN": " 123 ", "Time_Date": "201510",
        "Events_Anomaly": "Conflict NMAC; Critical ;",
        "Aircraft 1.9_Flight Phase": "Cruise",
        "Aircraft 1.2_Make Model Name": "B737-800",
        "Report 1.2_Synopsis": "A synopsis.",
        "Report 1_Narrative": " First account. ",
        "Report 2_Narrative": "Second account.",
    }


def test_mapping_and_hash(raw):
    report = normalize(raw)
    assert report.acn == "123"
    assert (report.report_month, report.report_year) == ("2015-10", 2015)
    assert report.narrative == "— Report 1 —\nFirst account.\n\n— Report 2 —\nSecond account."
    assert report.anomaly_codes == ["Conflict NMAC", "Critical"]
    assert report.aircraft_category == "B737-800"
    assert report.content_hash == normalize(dict(reversed(list(raw.items())))).content_hash
    assert report.content_hash != replace(report, synopsis="Changed").content_hash


@pytest.mark.parametrize("field,value", [
    ("Time_Date", "201513"), ("Time_Date", "20151001"),
    ("acn_num_ACN", ""), ("acn_num_ACN", None), ("Report 1_Narrative", 42),
])
def test_invalid_values_fail(raw, field, value):
    raw[field] = value
    with pytest.raises(ValueError):
        normalize(raw)


def test_schema_drift_fails(raw):
    raw["surprise"] = ""
    with pytest.raises(ValueError, match="unknown"):
        normalize(raw)
    del raw["surprise"]
    del raw["Report 2_Narrative"]
    with pytest.raises(ValueError, match="missing"):
        normalize(raw)


def test_empty_narratives_dropped_and_second_only_kept(raw):
    raw["Report 1_Narrative"] = " "
    assert normalize(raw).narrative == "— Report 2 —\nSecond account."
    raw["Report 2_Narrative"] = None
    assert normalize(raw) is None


def test_settings_prefix_and_secrets(monkeypatch):
    monkeypatch.setenv("EMBED_QUERY_PREFIX", "custom prefix: ")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    settings = Settings.from_env()
    assert settings.embed_query_prefix == "custom prefix: "
    assert "test-secret" not in repr(settings)
