from src.domain.maps.spec import TABLE_PRESETS, validate_table_size


def test_table_presets_standard_massive():
    assert TABLE_PRESETS["standard"]["width"] == 120
    assert TABLE_PRESETS["massive"]["width"] == 180


def test_custom_table_validation():
    assert validate_table_size(100, 80) is True
    assert validate_table_size(0, 80) is False
