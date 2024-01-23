import streamlit as st

from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen
from utils.model_session_state import ModelSessionState

st.set_page_config(layout="wide")

st.title("Schema Matching for Health Data using Foundation Models")

# Load session state, creating a new object if none exists
session_state_obj = st.session_state.get("session_state", None)
if session_state_obj is None:
    st.session_state["session_state"] = session_state_obj = ModelSessionState()


with st.sidebar:
    # provide ability to reset the app
    if st.button("Reset App"):
        # Delete all the items in streamlit session state
        for key in st.session_state.keys():
            del st.session_state[key]
        # Create a new object to store session state
        st.session_state["session_state"] = session_state_obj = ModelSessionState()
        st.rerun()
    
    # Select result version(s) to visualize
    num_exps = len(session_state_obj.all_results)
    if num_exps >= 1:
        selected = st.selectbox("Selected result", options=reversed([result.name for result in session_state_obj.all_results]), index=0)
        if selected is not None:
            session_state_obj.result = next(result for result in session_state_obj.all_results if result.name == selected)
        else:
            session_state_obj.result = None
            session_state_obj.compare_to = None
        # only show compare-to option if at least 2 experiments exist. Note that this can be None to disable comparison
        if selected is not None and num_exps >= 2:
            compare_to = st.selectbox("Compare to", options=reversed([result.name for result in session_state_obj.all_results]), index=None)
            if compare_to is not None:
                session_state_obj.compare_to = next(result for result in session_state_obj.all_results if result.name == compare_to)
            else:
                session_state_obj.compare_to = None

create_load_screen(session_state_obj)

create_visualize_screen(session_state_obj)
