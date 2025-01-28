from collections.abc import Callable
from typing import Any, Dict, List, Set

import streamlit as st
from st_cytoscape import cytoscape
import textdistance as td

from utils.models import Answer, Attribute, AttributePair, Result, TaskScope, Vote
from utils.model_session_state import ModelSessionState


def get_ngrams(s: str, n: int = 3) -> Set[str]:
    # as by [Sun et al.](www.doi.org/10.12733/jics20105420)
    full_s = f"{'#' * (n-1)}{s}{'%' * (n-1)}"
    return {full_s[i : i + n] for i in range(len(full_s) - n + 1)}


COLOR_MAP = {
    "baseline": "#bfbfbf",
    "1-to-1": "#E69F00",
    "1-to-N": "#009E73",
    "N-to-1": "#56B4E9",
    "N-to-M": "#F0E442",
}

BASELINES = {
    "Jaro-Winkler": td.jaro_winkler.normalized_similarity,
    "Levenshtein": td.levenshtein.normalized_similarity,
    "Monge-Elkan": td.monge_elkan.normalized_similarity,
    "3-gram": lambda a, b: td.sorensen.normalized_similarity(
        get_ngrams(a, 3), get_ngrams(b, 3)
    ),
}


def create_evaluation_screen(mss: ModelSessionState):
    if mss.result is None:
        return
    # TODO: check if ground truth is there
    # TODO: add metrics calculation
    st.header("Evaluation")

    result = mss.result
    selected_source = [
        attr
        for attr in result.parameters.source_relation.attributes
        if f"src_{attr.name}" in mss.selected_attrs
    ]
    selected_target = [
        attr
        for attr in result.parameters.target_relation.attributes
        if f"trg_{attr.name}" in mss.selected_attrs
    ]

    left, right = st.columns(2)
    with left:
        scopes_to_show = st.pills(
            "Compare task scopes:",
            ["1-to-N", "N-to-1", "N-to-M"] + ["1-to-1"],
            selection_mode="multi",
            default=["1-to-N", "N-to-1"],
        )
        # TODO: calculate the metrics here
        # idea: can I copy-pasta my evaluation heatmaps here? there is a st.plotly_chart elements, which takes a figure. check my analysis notebooks whether that is possible and easy to do

    with right:
        baseline_to_use = st.selectbox(
            "Choose a baseline string similarity metric:",
            list(BASELINES.keys()),
            index=3,
        )
        baseline_values = {}
        if len(selected_source) == 1:
            baseline_selected = selected_source[0]
            baseline_values = _get_attributes_baseline(
                selected_source[0],
                (
                    selected_target
                    if selected_target
                    else result.parameters.target_relation.attributes
                ),
                BASELINES[baseline_to_use],
            )
        elif len(selected_target) == 1:
            baseline_selected = selected_target[0]
            baseline_values = _get_attributes_baseline(
                selected_target[0],
                (
                    selected_source
                    if selected_source
                    else result.parameters.source_relation.attributes
                ),
                BASELINES[baseline_to_use],
            )
        # TODO: calculate metrics here
        # idea: see above, take the analysis notebooks
        if baseline_values:
            st.text(f"{baseline_to_use} similarity of {baseline_selected.name}:")
            st.table(baseline_values)
        else:
            st.info(
                (
                    "Select a single source attribute or a single target attribute "
                    "to view detailed string similarities."
                )
            )


def _get_attributes_baseline(
    attribute: Attribute, others: List[Attribute], metric: Callable[[str, str], float]
) -> Dict[Attribute, float]:
    return {
        other_attr.name: metric(attribute.name, other_attr.name)
        for other_attr in others
    }


def _which_scope_is(answer: Answer) -> TaskScope:
    if len(answer.attributes.sources) > 1:
        if len(answer.attributes.targets) > 1:
            return TaskScope.nToN
        return TaskScope.nToOne
    if len(answer.attributes.targets) > 1:
        return TaskScope.oneToN
    return TaskScope.oneToOne


def _get_votes_by_scope(
    result: Result, scope: TaskScope
) -> Dict[AttributePair, List[Vote]]:
    votes = {}
    for pair, result_pair in result.pairs.items():
        votes[pair] = []
        for vote in result_pair.votes:
            if _which_scope_is(vote.answer) == scope:
                votes[pair].append(vote.vote)
    return votes
