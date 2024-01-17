import streamlit as st

from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen
from utils.session_state import SessionState

st.title("Schema Matching for Health Data using Foundation Models")

# Load session state, creating a new object if none exists
session_state_obj = st.session_state.get("session_state", None)
if session_state_obj is None:
    st.session_state["session_state"] = session_state_obj = SessionState()

# provide ability to reset the app
if st.button("Reset App"):
    st.session_state["session_state"] = session_state_obj = SessionState()
    
create_load_screen(session_state_obj)

create_visualize_screen()
    

def ugly_test_method():
    import json
    from utils.backend import schema_match
    from utils.models import Attribute, Parameters, Relation
    with open("test_inputs/Patients_Person.json", "r") as f:
        test_input = json.load(f)
    params = Parameters(
        source_relation=Relation(
            name=test_input["source_relation"]["name"],
            attributes=[
                Attribute(
                    name=attr["name"],
                    description=attr["description"],
                ) for attr in test_input["source_relation"]["attributes"]
            ],
            description=test_input["source_relation"]["description"],
        ),
        target_relation=Relation(
            name=test_input["target_relation"]["name"],
            attributes=[
                Attribute(
                    name=attr["name"],
                    description=attr["description"],
                ) for attr in test_input["target_relation"]["attributes"]
            ],
            description=test_input["target_relation"]["description"],
        )
    )
    result = schema_match(parameters=params)
    st.write(result)


st.button("Test Run", on_click=ugly_test_method)
