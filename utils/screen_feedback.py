import streamlit as st
from utils.model_session_state import ModelSessionState
from utils.models import Feedback


def create_feedback_screen(mss: ModelSessionState):

    # Callback functions for when a field is changed.
    # Note that values shown in text fields are internally stored in the streamlit session state under the corresponding widget key.
    def on_change_feedback(feedback: Feedback, session_key: str):
        feedback.general = st.session_state[session_key]

    # Already init the feedback object if it does not exist yet (even if this section is not shown due to no experiment being run yet!)
    if mss.feedback is None:
        mss.feedback = Feedback(general="")

    # Only show this part if at least one experiment executed before
    if len(mss.all_results) == 0:
        return

    st.header("Feedback")
    feedback = mss.feedback
    fb_key = "general_feedback"
    if fb_key not in st.session_state:
        st.session_state[fb_key] = feedback.general
    st.text_area("Feedback", key=fb_key, on_change=on_change_feedback, args=(feedback, fb_key))

    if mss.result is not None:
        with st.expander(f"Feedback used in {mss.result.name}"):
            st.text_area("Feedback", value=mss.result.parameters.feedback.general, disabled=True, key=f"{mss.result.name}.feedback.result")
    if mss.compare_to is not None:
        with st.expander(f"Feedback used in {mss.compare_to.name}"):
            st.text_area("Feedback", value=mss.compare_to.parameters.feedback.general, disabled=True, key=f"{mss.compare_to.name}.feedback.compare_to")
