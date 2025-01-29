from collections.abc import Callable
from typing import Dict, List, Set

import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import precision_recall_fscore_support
import streamlit as st
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
    st.header("Evaluation")

    # TODO: obtain the ground truth
    ground_truth = [("gender", "sex"), ("registerdate", "birthdate")]

    result = mss.result

    # choose the parameters to use
    left, right = st.columns(2)
    with left:
        scopes_to_show = st.pills(
            "Select task scopes for comparison:",
            ["1-to-N", "N-to-1", "N-to-M"] + ["1-to-1"],
            selection_mode="multi",
            default=["1-to-N", "N-to-1"],
        )

    with right:
        baseline_to_use = st.selectbox(
            "Choose a baseline string similarity metric:",
            list(BASELINES.keys()),
            index=3,
        )
        # TODO: if possible, choose the best threshold as done in the experiments
        # idea: between creating evaluation and adding all scopes, I could make the check and change the value of this slider (don't forget to also change baseline_threshold then)
        baseline_threshold = st.slider("Choose a threshold:", 0.0, 1.0, 0.5)

    # show evaluation metrics
    baseline_values = {
        attribute_pair: BASELINES[baseline_to_use](
            attribute_pair.source.name, attribute_pair.target.name
        )
        for attribute_pair, _ in result.pairs.items()
    }
    evaluation = [
        {
            "task_scope": baseline_to_use,
            "source": attribute_pair.source.name,
            "target": attribute_pair.target.name,
            "decision": "yes" if similarity >= baseline_threshold else "no",
            "benchmark": (attribute_pair.source.name, attribute_pair.target.name)
            in ground_truth,
        }
        for attribute_pair, similarity in baseline_values.items()
    ]
    for scope in scopes_to_show:
        for attribute_pair, votes in _get_votes_by_scope(result, scope).items():
            if votes:
                vote_count = pd.Series(votes).value_counts()
                if vote_count.max() == 1:
                    decision = "unknown"
                else:
                    decision = vote_count.idxmax()
            else:
                decision = "unknown"
            evaluation.append(
                {
                    "task_scope": scope,
                    "source": attribute_pair.source.name,
                    "target": attribute_pair.target.name,
                    "decision": decision,
                    "benchmark": (
                        attribute_pair.source.name,
                        attribute_pair.target.name,
                    )
                    in ground_truth,
                }
            )
    evaluation = pd.DataFrame(evaluation)
    score_columns = [baseline_to_use] + sorted(scopes_to_show)
    scores = evaluation.groupby("task_scope").apply(
        lambda group: pd.Series(
            precision_recall_fscore_support(
                group["benchmark"],
                group["decision"] == "yes",
                average="binary",
                pos_label=True,
                zero_division=0.0,
            ),
            index=["precision", "recall", "f1-score", "support"],
        ),
        include_groups=False,
    ).loc[score_columns]
    labels = [
        [
            f"{f1_score:.3f} ({scores.loc[scope, 'precision']:.2f}, {scores.loc[scope, 'recall']:.2f})"
            for scope, f1_score in scores["f1-score"].items()
        ]
    ]
    fig = go.Figure(
        data=go.Heatmap(
            x=score_columns,
            y=[""],
            z=[scores["f1-score"].values],
            text=labels,
            texttemplate="%{text}",
            textfont={"size": 20},
            colorscale="PRGn",
            zmin=-1.0,
            zmax=1.0,
            showscale=False,
        ),
        layout={
            "title": "F1-score (precision, recall)",
            "height": 250,
            "width": 1000,
            "yaxis": {"autorange": "reversed"},
        },
    )
    st.plotly_chart(fig, use_container_width=True)
    decisiveness = evaluation.groupby("task_scope").apply(
        lambda group: pd.Series(
            1 - group[group["decision"] == "unknown"].shape[0] / group.shape[0],
            index=["decisiveness"],
        ),
        include_groups=False,
    ).loc[score_columns]
    fig = go.Figure(
        data=go.Heatmap(
            x=score_columns,
            y=[""],
            z=[decisiveness["decisiveness"].values],
            texttemplate="%{z:.2f}",
            textfont={"size": 20},
            colorscale="PRGn",
            zmin=-1.0,
            zmax=1.0,
            showscale=False,
        ),
        layout={
            "title": "Decisiveness (fraction of non-unknown votes)",
            "height": 250,
            "width": 1000,
            "yaxis": {"autorange": "reversed"},
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    # show more details
    st.subheader("More details")
    left, right = st.columns(2)
    with left:
        for scope in sorted(scopes_to_show):
            with st.expander(scope):
                st.caption("false positives")
                st.table(
                    evaluation.query(
                        "(task_scope == @scope)"
                        " and (decision == 'yes')"
                        " and ~benchmark"
                    )
                )
                st.caption("false negatives")
                st.table(
                    evaluation.query(
                        "(task_scope == @scope)"
                        " and (decision == 'no')"
                        " and benchmark"
                    )
                )
                st.caption("unknowns")
                st.table(
                    evaluation.query(
                        "(task_scope == @scope)"
                        " and (decision == 'unknown')"
                    )
                )

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
    with right:
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
        if baseline_values:
            st.text(f"{baseline_to_use} similarity of {baseline_selected.name}:")
            st.table(
                [
                    {
                        "attribute": attr,
                        "similarity": sim,
                        "match": sim >= baseline_threshold,
                    }
                    for attr, sim in baseline_values.items()
                ]
            )
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
