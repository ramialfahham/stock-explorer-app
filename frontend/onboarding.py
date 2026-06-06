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
  <p class="welcome-kicker">Welcome to Stock Swipe</p>
  <p class="welcome-lead">
    Browse company cards with five beginner-friendly metrics. Save ones you want to revisit —
    skip the rest for now.
  </p>
  <ul class="welcome-list">
    <li><strong>Save</strong> adds a company to your Saved tab on this device.</li>
    <li><strong>Not interested right now</strong> moves to the next card.</li>
    <li>Nothing is investment advice — use cards to learn, then dig deeper elsewhere.</li>
  </ul>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Got it — show me stocks", type="primary", use_container_width=True):
        dismiss_onboarding()
        st.rerun()
    return True
