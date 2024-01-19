import json
import time
import streamlit as st
from utils.model_session_state import ModelSessionState
from utils.models import Relation, Attribute, Parameters
from utils.backend import schema_match

def create_load_screen(mss: ModelSessionState):
    
    st.header("Input data")

    # if editing still possible: allow uploading a file
    if not mss.input_fixed:
        # unique id to refresh file upload on each rerun
        # without this, `uploaded_file` will remain a file pointer, thereby freshly overwriting the data on each run
        if "upload_id" not in st.session_state:
            st.session_state["upload_id"] = 0
        uploaded_file = st.file_uploader("Choose a file", type=["json"], key=f"upload.{st.session_state['upload_id']}")
        if uploaded_file is not None:
            st.session_state["upload_id"] += 1
            json_dict = json.load(uploaded_file)
            mss.source_relation = Relation.from_dict(json_dict["source_relation"])
            mss.target_relation = Relation.from_dict(json_dict["target_relation"])
            st.rerun()
            #st.info(f"Successfully loaded relations **{session_state.source_relation.name}** and **{session_state.target_relation.name}**")
    
    if mss.source_relation is not None:
        st.subheader(f"Source Relation: {mss.source_relation.name}")
        _display_relation(mss.source_relation)
    
    if mss.target_relation is not None:
        st.subheader(f"Target Relation: {mss.target_relation.name}")
        _display_relation(mss.target_relation)

    if mss.source_relation is not None and mss.target_relation is not None:
        if st.button("Run Schema Matching"):
            mss.input_fixed = True
            with st.spinner("Matching schemas..."):
                params = Parameters(
                    source_relation=mss.source_relation,
                    target_relation=mss.target_relation,
                )
                mss.result = schema_match(params)
                st.info("Debug info: manual sleep time for testing purposes!")
                time.sleep(4)
            st.rerun()


def _display_relation(relation: Relation, names_fixed: bool = False):
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

    # field for relation description
    rel_key_descr = f"{relation.name}.description"
    if rel_key_descr not in st.session_state:
        st.session_state[rel_key_descr] = relation.description
    st.text_area("Relation description", key=rel_key_descr, on_change=on_change_reldescr, args=(relation, rel_key_descr))
    
    # All atributes
    for i, attr in enumerate(relation.attributes):
        # Attribute name
        attr_key_name = f"{relation.name}.Attr{i}.name"
        if attr_key_name not in st.session_state:
            st.session_state[attr_key_name] = attr.name
        st.text_input(f"Attribute {i+1}", key=attr_key_name, on_change=on_change_attrname, args=(attr, attr_key_name), disabled=names_fixed)
        # Attribute description
        attr_key_descr = f"{relation.name}.Attr{i}.description"
        if attr_key_descr not in st.session_state:
            st.session_state[attr_key_descr] = attr.description
        st.text_area("description", key=attr_key_descr, on_change=on_change_attrdescr, args=(attr, attr_key_descr), label_visibility="collapsed")
        # Attribute included checkbox
        attr_key_incl = f"{relation.name}.Attr{i}.included"
        if attr_key_incl not in st.session_state:
            st.session_state[attr_key_incl] = attr.included
        st.checkbox("Include", key=attr_key_incl, on_change=on_change_attrincl, args=(attr, attr_key_incl), disabled=names_fixed)
