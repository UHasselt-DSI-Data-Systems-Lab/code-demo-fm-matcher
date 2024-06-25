import os
import json
from typing import Optional
import streamlit as st
from utils.model_session_state import ModelSessionState
from utils.models import Relation, Attribute, Result


def create_load_screen(mss: ModelSessionState):
    
    st.header("Input data")
    # if editing still possible: allow uploading a file
    if not mss.input_fixed:
        # unique id to refresh file upload on each rerun
        # without this, `uploaded_file` will remain a file pointer, thereby freshly overwriting the data on each run
        if "upload_id" not in st.session_state:
            st.session_state["upload_id"] = 0
        uploaded_file = st.file_uploader("Choose a file", type=["json"], key=f"upload.{st.session_state['upload_id']}")
        # hardcode a few example relations for presentation purposes
        st.markdown("Or choose a pre-defined example")
        example_file_names = list(filter(lambda f: f.endswith(".json"), os.listdir("test_inputs")))
        grid = [
            st.columns(4) for _ in range(len(example_file_names)//4+1)
        ]
        for i, file_name in enumerate(example_file_names):
            x, y = divmod(i, 4)
            with grid[x][y]:
                nice_name = {
                    "Admissions_Condition_Occurrence.json": "Admission -> Condition Occurrence",
                    "Admissions_Visit_Detail.json": "Admissions -> Visit Detail",
                    "Admissions_Visit_Occurrence.json": "Admissions -> Visit Occurrence",
                    "Diagnoses_ICD_Condition_Occurrence.json": "Diagnoses ICD -> Condition Occurrence",
                    "Labevents_Measurement.json": "Labevents -> Measurement",
                    "Patients_Person.json": "Patients -> Person",
                    "Prescriptions_Drug_Exposure.json": "Prescriptions -> Drug Exposure",
                    "Services_Visit_Detail.json": "Services -> Visit Detail",
                    "simple_example.json": "Simple Example",
                    "Transfers_Visit_Detail.json": "Transfers -> Visit Detail",
                }[file_name]
                chosen_name = st.button(
                    nice_name,
                    key=file_name,
                )
                if chosen_name:
                    uploaded_file = open(f"test_inputs/{file_name}", "rb")

        if uploaded_file is not None:
            st.session_state["upload_id"] += 1
            json_dict = json.load(uploaded_file)
            # load relations from json
            mss.source_relation = Relation.from_dict(json_dict["source_relation"])
            mss.target_relation = Relation.from_dict(json_dict["target_relation"])
            # set unique ids for each attribute
            for attr in mss.source_relation.attributes:
                attr.uid = mss.get_next_uid()
            for attr in mss.target_relation.attributes:
                attr.uid = mss.get_next_uid()
            st.rerun()
            #st.info(f"Successfully loaded relations **{session_state.source_relation.name}** and **{session_state.target_relation.name}**")
    
    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if mss.source_relation is not None:
            st.subheader(f"Source Relation: {mss.source_relation.name}")
            _display_relation(mss.source_relation, names_fixed=mss.input_fixed, result=mss.result, compare_to=mss.compare_to)
            _create_add_attribute_button(mss, "source")

    with col2:
        if mss.target_relation is not None:
            st.subheader(f"Target Relation: {mss.target_relation.name}")
            _display_relation(mss.target_relation, names_fixed=mss.input_fixed, result=mss.result, compare_to=mss.compare_to)
            _create_add_attribute_button(mss, "target")


def _create_add_attribute_button(mss: ModelSessionState, side: str) -> None:
    if not mss.input_fixed and st.button("Add attribute", key=f"add_{side}_attribute"):
        getattr(mss, f"{side}_relation").attributes.append(
            Attribute(
                name="Name...",
                description="Description...",
                included=False,
                uid=mss.get_next_uid(),
            )
        )
        st.rerun()


def _display_relation(relation: Relation, names_fixed: bool = False, result: Optional[Result] = None, compare_to: Optional[Result] = None):
    """Display a relation and allow editing."""
    # Callback functions for when a field is changed.
    # Note that values shown in text fields are internally stored in the streamlit session state under the corresponding widget key.
    def on_change_reldescr(relation: Relation, session_key: str):
        relation.description = st.session_state[session_key]
    def on_change_attrname(attr: Attribute, session_key: str):
        attr.name = st.session_state[session_key]
    def on_change_attrdescr(attr: Attribute, session_key: str):
        attr.description = st.session_state[session_key]
    def on_change_attrincl(attr: Attribute, session_key: str):
        attr.included = st.session_state[session_key]
    def on_click_attrrem(relation: Relation, attr: Attribute, session_key: str) -> None:
        relation.attributes.remove(attr)

    # field for relation description
    with st.expander("Relation details"):
        # description
        rel_key_descr = f"{relation.name}.description"
        if rel_key_descr not in st.session_state:
            st.session_state[rel_key_descr] = relation.description
        st.text_area("Relation description", key=rel_key_descr, on_change=on_change_reldescr, args=(relation, rel_key_descr))
        # versions used in previous experiments:
        if result is not None:
            if relation.name == result.parameters.source_relation.name:
                st.text_area(f"Description used in {result.name}", value=result.parameters.source_relation.description, disabled=True, key=f"{relation.name}.description.result")
            elif relation.name == result.parameters.target_relation.name:
                st.text_area(f"Description used in {result.name}", value=result.parameters.target_relation.description, disabled=True, key=f"{relation.name}.description.result")
        if compare_to is not None:
            if relation.name == compare_to.parameters.source_relation.name:
                st.text_area(f"Description used in {compare_to.name}", value=compare_to.parameters.source_relation.description, disabled=True, key=f"{relation.name}.description.compare_to")
            elif relation.name == compare_to.parameters.target_relation.name:
                st.text_area(f"Description used in {compare_to.name}", value=compare_to.parameters.target_relation.description, disabled=True, key=f"{relation.name}.description.compare_to")
        
    # All atributes
    for i, attr in enumerate(relation.attributes):
        # Attribute name
        attr_key_name = f"{relation.name}.Attr{i}.name"
        # TODO: what are those checks needed for?
        # if attr_key_name not in st.session_state:
        st.session_state[attr_key_name] = attr.name
        st.text_input(f"Attribute {i+1}", key=attr_key_name, on_change=on_change_attrname, args=(attr, attr_key_name), disabled=names_fixed)
        with st.expander("details"):
            # Attribute description
            attr_key_descr = f"{relation.name}.Attr{i}.description"
            # TODO: what are those checks needed for?
            # if attr_key_descr not in st.session_state:
            st.session_state[attr_key_descr] = attr.description
            st.text_area("description", key=attr_key_descr, on_change=on_change_attrdescr, args=(attr, attr_key_descr), label_visibility="collapsed")
            # Attribute included checkbox
            attr_key_incl = f"{relation.name}.Attr{i}.included"
            # TODO: what are those checks needed for?
            # if attr_key_incl not in st.session_state:
            st.session_state[attr_key_incl] = attr.included
            st.checkbox("Include", key=attr_key_incl, on_change=on_change_attrincl, args=(attr, attr_key_incl), disabled=names_fixed)
            attr_key_remove = f"{relation.name}.Attr{i}.remove"
            st.button("Remove", key=attr_key_remove, on_click=on_click_attrrem, args=(relation, attr, attr_key_remove))

            # show version of description from results and compare-to if available
            if result is not None and attr.uid is not None:
                attribute = _find_attribute(result, attr.uid)
                st.text_area(f"Description used in {result.name}", value=attribute.description, disabled=True, key=f"{relation.name}.Attr{attribute.uid}.description.result")
            if compare_to is not None and attr.uid is not None:
                attribute = _find_attribute(compare_to, attr.uid)
                st.text_area(f"Description used in {compare_to.name}", value=attribute.description, disabled=True, key=f"{relation.name}.Attr{attribute.uid}.description.compare_to")


def _find_attribute(result: Result, uid: int) -> Attribute:
    """find the attribute in the result, based on the uid"""
    for attr in result.parameters.source_relation.attributes:
        if attr.uid == uid:
            return attr
    for attr in result.parameters.target_relation.attributes:
        if attr.uid == uid:
            return attr
    raise ValueError(f"Attribute with uid {uid} not found in result")
