from tools import lookup, calculate

def test_calculate_multiplication():
    result = calculate(
        "48317 * 1.0947"
    )

    assert "result" in result


def test_calculate_division():
    result = calculate(
        "44675 / 921.4"
    )

    assert "result" in result


def test_calculate_import_attack():
    result = calculate(
        "__import__('os').system('echo hi')"
    )

    assert "error" in result


def test_calculate_class_attack():
    result = calculate(
        "(1).__class__"
    )

    assert "error" in result


def test_calculate_huge_power():
    result = calculate(
        "9**9**9"
    )

    assert "error" in result


def test_calculate_division_by_zero():
    result = calculate(
        "10 / 0"
    )

    assert result["error"] == "division by zero"


def test_lookup_current_population():
    result = lookup(
        "Tarnvale",
        "population"
    )

    assert "matches" in result

    text = " ".join(
        item["text"]
        for item in result["matches"]
    )

    assert "71,388" in text


def test_lookup_ignores_archived_profile():
    result = lookup(
        "Kelmarsh",
        "population"
    )

    sources = [
        item["source"]
        for item in result["matches"]
    ]

    assert "NR-04" in sources
    assert "NR-14" not in sources


def test_lookup_uses_brightwater_correction():
    result = lookup(
        "Brightwater",
        "area"
    )

    correction_sources = [
        item["source"]
        for item in result["corrections"]
    ]

    assert "NR-16" in correction_sources


def test_lookup_similar_names_are_separate():
    result1 = lookup(
        "Ossbridge",
        "population"
    )

    result2 = lookup(
        "Ossford",
        "population"
    )

    assert result1["district"] == "Ossbridge"
    assert result2["district"] == "Ossford"


def test_lookup_misspelled_name():
    result = lookup(
        "Ossbrige",
        "population"
    )

    assert "error" in result


def test_lookup_lindenmoor_water_unit():
    result = lookup(
        "Lindenmoor",
        "water use"
    )

    text = " ".join(
        item["text"]
        for item in result["matches"]
    )

    assert "2,151,400 cubic metres" in text

