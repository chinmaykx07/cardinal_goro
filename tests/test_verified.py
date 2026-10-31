import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
from verified import fill, check, render_or_fallback, indian_group

REC = dict(name="सुनीता पाटील", place="नाशिक", amount=1500, date=(30, 11, 2026), ref="RTS/2026/04521")
TPL = "{NAME} यांचा अर्ज क्र. {REF} {PLACE} केंद्रात {DATE} रोजी {AMOUNT} जमा करावे."


def test_fill_then_check_passes():
    assert check(fill(TPL, REC), REC) == []


def test_wrong_year_caught():
    bad = fill(TPL, REC).replace("२०२६", "२०२५")
    assert "date" in check(bad, REC)


def test_amount_digit_swap_caught():
    bad = fill(TPL, REC).replace("१,५००", "५,१००")
    assert "amount_or_extra_number" in check(bad, REC)


def test_extra_number_caught():
    assert "amount_or_extra_number" in check(fill(TPL, REC) + " ९९", REC)


def test_matra_change_caught_strictly():
    bad = fill(TPL, REC).replace("सुनीता", "सुनिता")
    assert any(f.startswith("missing:") for f in check(bad, REC))


def test_inflected_name_passes():
    text = fill("{NAME} यांना {PLACE}ला {REF} {DATE} {AMOUNT}", REC)
    assert check(text, REC) == []


def test_fallback_on_bad_draft():
    text, src = render_or_fallback("{NAME} {REF} {DATE} ५०० {AMOUNT}", TPL, REC)
    assert src == "template" and check(text, REC) == []


def test_unknown_slot_falls_back():
    _, src = render_or_fallback("{NAME} {BOGUS}", TPL, REC)
    assert src == "template"


def test_indian_grouping():
    assert indian_group(1250000) == "12,50,000"
    assert indian_group(1500) == "1,500"
    assert indian_group(999) == "999"
    assert indian_group(123456789) == "12,34,56,789"


def test_amount_filled_in_indian_grouping():
    rec = dict(REC, amount=1250000)
    text = fill(TPL, rec)
    assert "१२,५०,०००" in text and check(text, rec) == []


def test_bad_template_abstains_instead_of_sending():
    text, source = render_or_fallback("{FOO}", TPL + " ९९", REC)
    assert (text, source) == (None, "abstain")
