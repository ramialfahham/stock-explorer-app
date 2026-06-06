"""First-run landing page for new visitors."""

from __future__ import annotations

import streamlit as st

from brand import PRODUCT_NAME, PRODUCT_TAGLINE
from browser_storage import dismiss_onboarding, is_onboarding_dismissed, onboarding_ready


def render_landing() -> bool:
    """Show full landing on first visit. Returns True while landing is visible."""
    if not onboarding_ready() or is_onboarding_dismissed():
        return False

    st.markdown(
        f"""
<div class="ss-landing">
  <p class="ss-landing-eyebrow">Welcome</p>
  <h1 class="ss-landing-title">{PRODUCT_NAME}</h1>
  <p class="ss-landing-tagline">{PRODUCT_TAGLINE}</p>
  <ul class="ss-landing-points">
    <li>Browse company cards with five key fundamentals explained in plain language</li>
    <li>Save companies you want to follow — skips mean “not for me right now”</li>
    <li>No account needed; your list stays on this device</li>
  </ul>
  <p class="ss-landing-disclaimer">Not investment advice.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    if st.button("Start exploring", type="primary", use_container_width=True):
        dismiss_onboarding()
        st.rerun()
    return True
