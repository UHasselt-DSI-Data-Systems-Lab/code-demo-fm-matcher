from copy import deepcopy
import hmac

import streamlit as st

from utils.backend import schema_match, get_available_openai_models
from utils.models import Parameters, Relation, Vote
from utils.screen_feedback import create_feedback_screen
from utils.screen_evaluation import create_evaluation_screen
from utils.screen_load import create_load_screen
from utils.screen_visualize import create_visualize_screen
from utils.model_session_state import ModelSessionState
from utils.storage import get_similar_results_by_parameters

st.set_page_config(layout="wide")

st.title("LLM-Matcher")
st.text("Schema Matching for Health Data using Large Language Models")


def check_password() -> bool:
    """Use the most simple login solution as described by streamlit."""

    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    st.text_input(
        "Give me the magic phrase",
        type="password",
        on_change=password_entered,
        key="password",
    )

    if "password_correct" in st.session_state:
        st.error("Password incorrect")

    return False


def password_set() -> bool:
    """Check whether a password is set via streamlits secrets management."""
    try:
        return "password" in st.secrets
    except FileNotFoundError:
        # indicates that no secrets.toml is available, thus no password is set
        return False


if password_set() and not check_password():
    st.stop()


# Load session state, creating a new object if none exists
session_state_obj = st.session_state.get("session_state", None)
if session_state_obj is None:
    st.session_state["session_state"] = session_state_obj = ModelSessionState()


def _is_input_valid(relation: Relation) -> bool:
    if relation is None:
        return False
    attrs = set()
    for attr in relation.attributes:
        if attr.name in attrs:
            return False
        attrs = attrs.union({attr.name})
    return True


def _submit_button(mss: ModelSessionState):
    submittable = True
    if not _is_input_valid(mss.source_relation) or not _is_input_valid(
        mss.target_relation
    ):
        submittable = False
    button_text = "Run Schema Matching Again"
    if mss.result is None:
        button_text = "Run Schema Matching"
    if st.button(button_text, disabled=not submittable):
        mss.input_fixed = True
        with st.spinner("Matching schemas..."):
            # create a deepcopy of all parameters to avoid changing params
            # (e.g. descriptions) of older experiments in the visualization
            # when changing descriptions in the input
            params = Parameters(
                source_relation=deepcopy(mss.source_relation),
                target_relation=deepcopy(mss.target_relation),
                feedback=deepcopy(mss.feedback),
                llm_model=mss.selected_llm,
            )
            result = schema_match(params)
            mss.result = result
        st.rerun()


def _create_sql_button(mss: ModelSessionState) -> None:
    if mss.result is None:
        return
    if st.button("Create SQL"):
        target_attributes = []
        select_lines = []
        for attr_pair, result in mss.result.pairs.items():
            if (
                sum([1 if d.vote == Vote.YES else 0 for d in result.votes])
                >= st.session_state["edge_threshold_slider"]
            ):
                target_attributes.append(f"  {attr_pair.target.name}")
                select_lines.append(
                    f"  {attr_pair.source.name} AS {attr_pair.target.name}"
                )
        sql_string = (
            f"INSERT INTO {mss.target_relation.name} (\n"
            f"{',\n'.join(target_attributes)}"
            "\n)\n"
            "SELECT\n"
            f"{',\n'.join(select_lines)}"
            f"\nFROM {mss.source_relation.name};"
        )
        st.code(
            body=sql_string,
            language="sql",
            line_numbers=True,
        )


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

    valid_llms = get_available_openai_models()
    llm_selected = st.selectbox(
        "Select an LLM to use",
        options=valid_llms,
        index=0,
    )
    if llm_selected in valid_llms:
        session_state_obj.selected_llm = llm_selected

    # Select result version(s) to visualize
    if session_state_obj.result:
        # similar experiments include the current experiment itself!
        similar_experiments = get_similar_results_by_parameters(
            session_state_obj.result.parameters
        )
        selected_index = None
        for i, e in enumerate(similar_experiments):
            if e.digest() == session_state_obj.result.digest():
                selected_index = i
        selected = st.selectbox(
            "Selected result",
            options=[r.name for r in similar_experiments],
            index=selected_index,
        )
        if selected is not None:
            session_state_obj.result = next(
                filter(lambda r: r.name == selected, similar_experiments)
            )
        else:
            session_state_obj.result = None
            session_state_obj.compare_to = None
        # only show compare-to option if at least 2 experiments exist.
        # Note that this can be None to disable comparison
        if selected is not None and len(similar_experiments) >= 2:
            compare_to = st.selectbox(
                "Compare to",
                options=[
                    result.name
                    for result in filter(
                        lambda r: r.name != selected, similar_experiments
                    )
                ],
                index=None,
            )
            if compare_to is not None and (compare_to != selected):
                session_state_obj.compare_to = next(
                    filter(lambda r: r.name == compare_to, similar_experiments)
                )
            else:
                session_state_obj.compare_to = None

# Data loading part
create_load_screen(session_state_obj)

# Data visualization part
create_visualize_screen(session_state_obj)

# Evaluation part
create_evaluation_screen(session_state_obj)

# Feedback part
create_feedback_screen(session_state_obj)

st.divider()

# (re)submit button
_submit_button(session_state_obj)
_create_sql_button(session_state_obj)
