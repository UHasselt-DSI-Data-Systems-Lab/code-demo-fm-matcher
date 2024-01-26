from copy import deepcopy
import time
import streamlit as st
from utils.backend import schema_match
from utils.models import Parameters
from utils.screen_feedback import create_feedback_screen

from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen
from utils.model_session_state import ModelSessionState

st.set_page_config(layout="wide")

st.title("Schema Matching for Health Data using Foundation Models")

# Load session state, creating a new object if none exists
session_state_obj = st.session_state.get("session_state", None)
if session_state_obj is None:
    st.session_state["session_state"] = session_state_obj = ModelSessionState()

def _submit_button(mss: ModelSessionState):
    if mss.source_relation is not None and mss.target_relation is not None:
            st.divider()
            button_text = "Run Schema Matching"
            if len(mss.all_results) > 0:
                button_text = "Run Schema Matching Again"
            if st.button(button_text):
                mss.input_fixed = True
                with st.spinner("Matching schemas..."):
                    # create a deepcopy of all parameters to avoid changing params (e.g. descriptions) of older experiments in the visualization when changing descriptions in the input
                    params = Parameters(
                        source_relation=deepcopy(mss.source_relation),
                        target_relation=deepcopy(mss.target_relation),
                        feedback=deepcopy(mss.feedback)
                    )
                    result = schema_match(params)
                    #st.info("Debug info: manual sleep time for testing purposes!")
                    #time.sleep(1)
                    # Change the name of the result to something unique
                    result.name = f"Experiment {mss.get_next_experiment_id()}"
                    mss.all_results.append(result)
                st.rerun()

# The sidebar is used to reset the app and select the result to visualize
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

# Data loading part
create_load_screen(session_state_obj)

# Data visualization part
create_visualize_screen(session_state_obj)

create_feedback_screen(session_state_obj)

# (re)submit button
_submit_button(session_state_obj)
