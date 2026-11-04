"""Local text inputs that update Streamlit while the user types."""

from pathlib import Path

import streamlit.components.v1 as components


_input = components.declare_component(
    "live_editor", path=str(Path(__file__).parent / "live_editor")
)


def live_text(label: str, value: str, *, key: str, multiline: bool = False) -> str:
    return _input(
        label=label, value=value, multiline=multiline,
        key=key, default=value,
    )
