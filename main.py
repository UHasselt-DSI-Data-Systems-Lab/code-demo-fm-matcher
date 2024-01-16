import streamlit as st

from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen

from utils.request import Request

st.title("Schema Matching for Health Data using Foundation Models")
st.write("This will be an actual demo some day.")

with st.expander("Load Data"):
    create_load_screen()

with st.expander("Results"):
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
