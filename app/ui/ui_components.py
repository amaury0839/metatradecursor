"""
Reusable UI components for the Streamlit dashboard.
"""

from __future__ import annotations

from typing import Iterable, Dict, Any, Optional

import streamlit as st


def section_header(title: str, subtitle: Optional[str] = None) -> None:
    st.markdown(f"<div class=\"section-title\">{title}</div>", unsafe_allow_html=True)
    if subtitle:
        st.caption(subtitle)


def stat_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
<div class="stat-card">
  <div class="stat-label">{label}</div>
  <div class="stat-value">{value}</div>
  <div style="color: var(--subtle); font-size: 0.85rem;">{note}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def metric_grid(items: Iterable[Dict[str, Any]], columns: int = 4) -> None:
    cols = st.columns(columns)
    for idx, item in enumerate(items):
        with cols[idx % columns]:
            stat_card(
                item.get("label", "Metric"),
                item.get("value", "N/A"),
                item.get("note", ""),
            )


def badge(text: str, tone: str = "neutral") -> None:
    tone_map = {
        "positive": "#2fbf8f",
        "warning": "#f7b267",
        "negative": "#d64545",
        "neutral": "#c8d0da",
    }
    color = tone_map.get(tone, tone_map["neutral"])
    st.markdown(
        f"""
<span class="chip" style="background: rgba(255,255,255,0.12); color: {color};">
  {text}
</span>
        """,
        unsafe_allow_html=True,
    )


def empty_state(title: str, body: str) -> None:
    st.markdown(
        f"""
<div class="soft-panel">
  <strong>{title}</strong><br/>
  {body}
</div>
        """,
        unsafe_allow_html=True,
    )
