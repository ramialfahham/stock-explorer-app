"""First-run welcome panel for new visitors."""

from __future__ import annotations

import streamlit as st

from browser_storage import dismiss_onboarding, is_onboarding_dismissed, onboarding_ready


def render_welcome() -> bool:
    """Show dismissible welcome on first visit. Returns True while panel is visible."""
    if not onboarding_ready() or is_onboarding_dismissed():
        return False

    st.markdown(
        """
<div class="welcome-panel">
  <p class="welcome-lead">
    Browse company cards with plain-language fundamentals. Save what you want to revisit —
    everything stays on this device. Not investment advice.
  </p>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Show me stocks", type="primary", use_container_width=True):
        dismiss_onboarding()
        st.rerun()
    return True
