import json
import streamlit as st
from utils.session_state import SessionState
from utils.models import Relation

def create_load_screen(session_state: SessionState):
    
    st.header("Load Data")

    # if editing still possible: allow uploading a file
    if not session_state.input_fixed:
        uploaded_file = st.file_uploader("Choose a file", type=["json"])
        if uploaded_file is not None:
            json_dict = json.load(uploaded_file)
            session_state.source_relation = Relation.from_dict(json_dict["source_relation"])
            session_state.target_relation = Relation.from_dict(json_dict["target_relation"])
            st.info(f"Successfully loaded relations **{session_state.source_relation.name}** and **{session_state.target_relation.name}**")
    
    if session_state.source_relation is not None:
        st.subheader(f"Source Relation: {session_state.source_relation.name}")
        session_state.source_relation = _display_relation(session_state.source_relation)
    
    if session_state.target_relation is not None:
        st.subheader(f"Source Relation: {session_state.target_relation.name}")
        session_state.target_relation = _display_relation(session_state.target_relation)

    if session_state.source_relation is not None and session_state.target_relation is not None:
        if st.button("submit"):
            session_state.input_fixed = True
            st.info("Succesfully submitted.")


def _display_relation(relation: Relation) -> Relation:
    """Display a relation and allow editing. Changes are returned as a new relation"""
    relation.description = st.text_area("Relation description:", relation.description)
    src_data = relation.to_dict()
    src_data["attributes"] = st.data_editor(
        src_data["attributes"],
        num_rows="dynamic",
        use_container_width=True)
    relation = Relation.from_dict(src_data)
    st.info(f"Debug info: attributes: {','.join([a.name for a in relation.attributes])}")
    return relation
