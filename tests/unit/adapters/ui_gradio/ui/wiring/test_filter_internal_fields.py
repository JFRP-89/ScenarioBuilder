"""Test internal fields filtering in preview."""

from adapters.ui_gradio.ui.wiring._generate._preview import _filter_internal_fields


class TestFilterInternalFields:
    """Test that internal fields are correctly filtered from preview display."""

    def test_filter_removes_underscore_prefixed_fields(self):
        """Fields starting with _ should be removed."""
        preview_data = {
            "name": "Test",
            "seed": 123,
            "mode": "casual",
            "_payload": {"some": "data"},
            "_actor_id": "user123",
        }

        result = _filter_internal_fields(preview_data)

        assert "name" in result
        assert "seed" in result
        assert "mode" in result
        assert "_payload" not in result
        assert "_actor_id" not in result

    def test_filter_removes_is_replicable(self):
        """is_replicable should be filtered as it's an internal config flag."""
        preview_data = {
            "name": "Test",
            "seed": 123,
            "is_replicable": True,
            "mode": "casual",
        }

        result = _filter_internal_fields(preview_data)

        assert "name" in result
        assert "seed" in result
        assert "mode" in result
        assert "is_replicable" not in result

    def test_filter_keeps_other_fields(self):
        """Regular fields should not be filtered."""
        preview_data = {
            "name": "Battle",
            "seed": 456,
            "mode": "matched",
            "armies": "Gondor vs Mordor",
            "deployment": "Test_01",
            "layout": "Test_02",
            "objectives": "Test_03",
            "visibility": "private",
        }

        result = _filter_internal_fields(preview_data)

        assert len(result) == len(preview_data)
        assert result == preview_data

    def test_filter_handles_empty_dict(self):
        """Empty dict should remain empty."""
        preview_data: dict = {}

        result = _filter_internal_fields(preview_data)

        assert result == {}

    def test_filter_all_internal_fields_together(self):
        """Test filtering with all internal fields present."""
        preview_data = {
            "name": "Test",
            "seed": 789,
            "mode": "casual",
            "is_replicable": True,
            "_payload": {"data": "hidden"},
            "_actor_id": "user456",
            "_some_other_internal": "value",
        }

        result = _filter_internal_fields(preview_data)

        assert len(result) == 3  # Only name, seed, mode
        assert result == {
            "name": "Test",
            "seed": 789,
            "mode": "casual",
        }
