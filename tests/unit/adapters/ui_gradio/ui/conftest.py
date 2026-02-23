"""Shared fixtures for tests/unit/adapters/ui_gradio/ui/."""

from __future__ import annotations

import gradio as gr
import pytest

from adapters.ui_gradio.ui.pages.create_scenario import build_create_page


@pytest.fixture(scope="module")
def create_ns():
    """Build the create-page namespace once for the whole module."""
    with gr.Blocks():
        return build_create_page()
