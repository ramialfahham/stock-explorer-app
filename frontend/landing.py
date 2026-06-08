"""First-run landing page for new visitors."""

from __future__ import annotations

import streamlit as st

from brand import LANDING_TAGLINE, PRODUCT_NAME
from browser_storage import dismiss_onboarding, is_onboarding_dismissed, onboarding_ready


def render_landing() -> bool:
    """Show full landing on first visit or when reopened from the menu."""
    show_from_menu = bool(st.session_state.get("show_landing"))
    if not show_from_menu and (not onboarding_ready() or is_onboarding_dismissed()):
        return False

    st.markdown(
        f"""
<div class="ss-landing">
  <p class="ss-landing-eyebrow">How it works</p>
  <h1 class="ss-landing-title">{PRODUCT_NAME}</h1>
  <p class="ss-landing-tagline">{LANDING_TAGLINE}</p>
  <ul class="ss-landing-points">
    <li>Each company snapshot shows five financial fundamentals with short context lines</li>
    <li>Filter by market and sector, browse a list, or walk one company at a time</li>
    <li>Save builds your learning list on this device — Not now skips for later</li>
    <li>No account — your list stays on this device</li>
  </ul>
  <p class="ss-landing-disclaimer">Not investment advice.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Start exploring", type="primary", use_container_width=True):
        if show_from_menu:
            st.session_state.pop("show_landing", None)
        else:
            dismiss_onboarding()
        st.rerun()
    return True
