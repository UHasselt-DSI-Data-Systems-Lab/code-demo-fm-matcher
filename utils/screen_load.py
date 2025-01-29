import os
import json
from typing import Dict, Optional

import pandas as pd
import streamlit as st

from utils.model_session_state import ModelSessionState
from utils.models import Relation, Attribute, AttributePair, Result, Side


def create_load_screen(mss: ModelSessionState):
    st.header("Input data")

    # create a set of default source & target relations
    if mss.source_relation is None:
        mss.source_relation = Relation(name="New source", side=Side.SOURCE)
    if mss.target_relation is None:
        mss.target_relation = Relation(name="New target", side=Side.TARGET)

    # if editing still possible: allow uploading a file
    if not mss.input_fixed:
        # unique id to refresh file upload on each rerun
        # without this, `uploaded_file` will remain a file pointer,
        # thereby freshly overwriting the data on each run
        if "upload_id" not in st.session_state:
            st.session_state["upload_id"] = 0
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["json"],
            key=f"upload.{st.session_state['upload_id']}",
        )
        # hardcode a few example relations for presentation purposes
        st.markdown("Or choose a pre-defined example")
        example_file_names = list(
            filter(lambda f: f.endswith(".json"), os.listdir("test_inputs"))
        )
        grid = [st.columns(4) for _ in range(len(example_file_names) // 4 + 1)]
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
                    ground_truth_filename = file_name[:-len(".json")] + "_ground_truth.csv"

        if uploaded_file is not None:
            st.session_state["upload_id"] += 1
            json_dict = json.load(uploaded_file)
            # load relations from json
            mss.source_relation = Relation.from_dict(json_dict["source_relation"])
            mss.target_relation = Relation.from_dict(json_dict["target_relation"])
            mss.ground_truth = list()
            if os.path.exists(os.path.join("test_inputs", ground_truth_filename)):
                gt_csv = pd.read_csv(os.path.join("test_inputs", ground_truth_filename))
                for _, row in gt_csv.iterrows():
                    ap = AttributePair(
                        _get_attribute_by_name(mss.source_relation, row["source"]),
                        _get_attribute_by_name(mss.target_relation, row["target"]),
                    )
                    mss.ground_truth.append(ap)
            st.rerun()

    col1, col2 = st.columns(2, gap="medium")
    with col1:
        if mss.source_relation is not None:
            st.subheader("Source Relation")
            _display_relation(
                mss.source_relation,
                names_fixed=mss.input_fixed,
                result=mss.result,
                compare_to=mss.compare_to,
                side=Side.SOURCE,
            )
            _create_add_attribute_button(mss, Side.SOURCE)

    with col2:
        if mss.target_relation is not None:
            st.subheader("Target Relation")
            _display_relation(
                mss.target_relation,
                names_fixed=mss.input_fixed,
                result=mss.result,
                compare_to=mss.compare_to,
                side=Side.TARGET,
            )
            _create_add_attribute_button(mss, Side.TARGET)

    st.subheader("Ground truth")
    st.text(
        (
            "To enable the evaluation functionality, provide the true matches"
            " between the source and the target attributes in the following list."
        )
    )
    if st.checkbox(
        "Enable ground truth", disabled=mss.input_fixed, value=mss.ground_truth_enabled
    ):
        mss.ground_truth_enabled = True
        _ground_truth_selection(mss)
    else:
        mss.ground_truth_enabled = False


def _get_attribute_by_name(
    relation: Relation, attribute_name: str
) -> Optional[Attribute]:
    for attr in relation.attributes:
        if attr.name == attribute_name:
            return attr
    return None


def _ground_truth_selection(mss: ModelSessionState) -> None:
    left, right, control = st.columns(3)
    with left:
        st.caption("source attributes")
        if not mss.input_fixed:
            source_attribute = st.selectbox(
                "choose a source attribute",
                options=[a.name for a in mss.source_relation.attributes],
                key=f"ground_truth_source_attribute_{len(mss.ground_truth)}",
                disabled=mss.input_fixed,
                label_visibility="collapsed",
            )
        for i, ap in enumerate(mss.ground_truth):
            st.text_input(
                "source attribute name",
                ap.source.name,
                disabled=True,
                key=f"ground_truth_source_attribute_{i}",
                label_visibility="collapsed",
            )

    with right:
        st.caption("target_attributes")
        if not mss.input_fixed:
            target_attribute = st.selectbox(
                "choose a target attribute",
                options=[a.name for a in mss.target_relation.attributes],
                key=f"ground_truth_target_attribute_{len(mss.ground_truth)}",
                disabled=mss.input_fixed,
                label_visibility="collapsed",
            )
        for i, ap in enumerate(mss.ground_truth):
            st.text_input(
                "target attribute name",
                ap.target.name,
                disabled=True,
                key=f"ground_truth_target_attribute_{i}",
                label_visibility="collapsed",
            )
    with control:
        st.caption("controls")
        if not mss.input_fixed:
            if st.button(
                "add",
                disabled=(
                    mss.input_fixed
                    or (source_attribute is None)
                    or (target_attribute is None)
                ),
            ):
                src_attr = _get_attribute_by_name(mss.source_relation, source_attribute)
                trg_attr = _get_attribute_by_name(mss.target_relation, target_attribute)
                if not src_attr or not trg_attr:
                    st.error("An unknown error has occured.")
                attr_pair = AttributePair(src_attr, trg_attr)
                if attr_pair in mss.ground_truth:
                    st.toast("This pair is already in the ground truth.")
                else:
                    mss.ground_truth.append(AttributePair(src_attr, trg_attr))
                    st.rerun()
        for ap in mss.ground_truth:
            remove_ap = st.button(
                "remove",
                key=f"remove_button_{ap.source.name}_{ap.target.name}",
                disabled=mss.input_fixed,
            )
            if remove_ap:
                mss.ground_truth.remove(ap)
                st.rerun()


def _create_add_attribute_button(mss: ModelSessionState, side: Side) -> None:
    if not mss.input_fixed and st.button(
        "Add attribute", key=f"add_{side.value}_attribute"
    ):
        getattr(mss, f"{side.value}_relation").attributes.append(
            Attribute(
                name="Name...",
                description="Description...",
                included=False,
            )
        )
        st.rerun()


def _display_relation(
    relation: Relation,
    names_fixed: bool = False,
    result: Optional[Result] = None,
    compare_to: Optional[Result] = None,
    side: Side = Side.SOURCE,
):
    """Display a relation and allow editing."""

    # Callback functions for when a field is changed.
    # Note that values shown in text fields are internally stored in the
    # streamlit session state under the corresponding widget key.
    def on_change_relname(relation: Relation, session_key: str) -> None:
        relation.name = st.session_state[session_key]

    def on_change_reldescr(relation: Relation, session_key: str) -> None:
        relation.description = st.session_state[session_key]

    def on_change_attrname(attr: Attribute, session_key: str) -> None:
        attr.name = st.session_state[session_key]

    def on_change_attrdescr(attr: Attribute, session_key: str) -> None:
        attr.description = st.session_state[session_key]

    def on_change_attrincl(attr: Attribute, session_key: str) -> None:
        attr.included = st.session_state[session_key]

    def on_click_attrrem(relation: Relation, attr: Attribute, session_key: str) -> None:
        relation.attributes.remove(attr)

    rel_key_name = f"{side.value}_relation_name"
    st.text_input(
        "Relation name",
        value=relation.name,
        key=rel_key_name,
        on_change=on_change_relname,
        args=(relation, rel_key_name),
        disabled=names_fixed,
    )
    # field for relation description
    with st.expander("Relation details"):
        # description
        rel_key_descr = f"{relation.name}.description"
        if rel_key_descr not in st.session_state:
            st.session_state[rel_key_descr] = relation.description
        st.text_area(
            "Relation description",
            key=rel_key_descr,
            on_change=on_change_reldescr,
            args=(relation, rel_key_descr),
        )
        # versions used in previous experiments:
        if result is not None:
            if relation.name == result.parameters.source_relation.name:
                st.text_area(
                    f"Description used in {result.name}",
                    value=result.parameters.source_relation.description,
                    disabled=True,
                    key=f"{relation.name}.description.result",
                )
            elif relation.name == result.parameters.target_relation.name:
                st.text_area(
                    f"Description used in {result.name}",
                    value=result.parameters.target_relation.description,
                    disabled=True,
                    key=f"{relation.name}.description.result",
                )
        if compare_to is not None:
            if relation.name == compare_to.parameters.source_relation.name:
                st.text_area(
                    f"Description used in {compare_to.name}",
                    value=compare_to.parameters.source_relation.description,
                    disabled=True,
                    key=f"{relation.name}.description.compare_to",
                )
            elif relation.name == compare_to.parameters.target_relation.name:
                st.text_area(
                    f"Description used in {compare_to.name}",
                    value=compare_to.parameters.target_relation.description,
                    disabled=True,
                    key=f"{relation.name}.description.compare_to",
                )

    attribute_counts = _count_attributes(relation)
    # All atributes
    for i, attr in enumerate(relation.attributes):
        # Attribute name
        attr_key_name = f"{side.value}.Attr{i}.name"
        st.text_input(
            f"Attribute {i+1}",
            key=attr_key_name,
            on_change=on_change_attrname,
            args=(attr, attr_key_name),
            disabled=names_fixed,
            value=attr.name,
        )
        if attribute_counts[attr.name] > 1:
            st.error("Attribute names have to be unique.")
        with st.expander(f"Attribute {i+1} details"):
            # Attribute description
            attr_key_descr = f"{side.value}.Attr{i}.description"
            st.text_area(
                "description",
                key=attr_key_descr,
                on_change=on_change_attrdescr,
                args=(attr, attr_key_descr),
                label_visibility="collapsed",
                value=attr.description,
            )
            # Attribute included checkbox
            attr_key_incl = f"{side.value}.Attr{i}.included"
            st.checkbox(
                "Include",
                key=attr_key_incl,
                on_change=on_change_attrincl,
                args=(attr, attr_key_incl),
                disabled=names_fixed,
                value=attr.included,
            )
            attr_key_remove = f"{side.value}.Attr{i}.remove"
            st.button(
                "Remove",
                key=attr_key_remove,
                on_click=on_click_attrrem,
                disabled=names_fixed,
                args=(relation, attr, attr_key_remove),
            )

            # show version of description from results and compare-to if available
            if result is not None:
                attribute = _find_attribute(result, relation, attr.name)
                st.text_area(
                    f"Description used in {result.name}",
                    value=attribute.description,
                    disabled=True,
                    key=f"{side.value}.Attr{i}.description.result",
                )
            if compare_to is not None:
                attribute = _find_attribute(compare_to, relation, attr.name)
                st.text_area(
                    f"Description used in {compare_to.name}",
                    value=attribute.description,
                    disabled=True,
                    key=f"{side.value}.Attr{i}.description.compare_to",
                )


def _count_attributes(relation: Relation) -> Dict[str, int]:
    """Count how many times an attribute name occurs per relation.
    Helpful to assess whether an input is valid."""
    count = {}
    for attribute in relation.attributes:
        if attribute.name not in count:
            count[attribute.name] = 0
        count[attribute.name] += 1
    return count


def _find_attribute(result: Result, relation: Relation, attr_name: str) -> Attribute:
    """find the attribute in the result, based on relation and name."""
    if relation.side == Side.SOURCE:
        attrs = result.parameters.source_relation.attributes
    else:
        attrs = result.parameters.target_relation.attributes
    for attr in attrs:
        if attr.name == attr_name:
            return attr
    raise ValueError(f"Attribute with name {attr_name} not found in result")
