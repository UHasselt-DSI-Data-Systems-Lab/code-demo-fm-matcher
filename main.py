import streamlit as st

from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen
from utils.model_session_state import ModelSessionState

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

create_load_screen(session_state_obj)

create_visualize_screen()

if session_state_obj.result is not None:
    st.header("Result")
    st.write(session_state_obj.result)
