from typing import Any, Optional
import streamlit as st
from st_cytoscape import cytoscape
from streamlit_extras.stylable_container import stylable_container
from utils.model_session_state import ModelSessionState
from utils.models import Attribute, AttributePair, Result, Vote

COLOR_YES = "#009E73"
COLOR_NO = "#E69F00"
COLOR_UNKNOWN = "#bfbfbf"

COLOR_YES_2 = "#56B4E9"
COLOR_NO_2 = "#F0E442"
COLOR_UNKNOWN_2 = "#4a4a4a"


def create_visualize_screen(mss: ModelSessionState):
    if mss.result is None:
        # st.warning("No results to visualize yet")
        return

    st.header("Results")

    result = mss.result
    compare_to = mss.compare_to

    # Selectors for visualized vote types
    # st.write("Show votes:")
    cols = st.columns(3)
    with cols[0]:
        with stylable_container(
            key="yes_button",
            css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_YES};border-color: {COLOR_YES};}}',
        ):
            show_yes = st.checkbox(
                f"Show yes-votes for {result.name}", value=True, key="vote_yes_checkbox"
            )
    with cols[1]:
        with stylable_container(
            key="no_button",
            css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_NO};border-color: {COLOR_NO};}}',
        ):
            show_no = st.checkbox(
                f"Show no-votes for {result.name}", value=True, key="vote_no_checkbox"
            )
    with cols[2]:
        with stylable_container(
            key="unknown_button",
            css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_UNKNOWN};border-color: {COLOR_UNKNOWN};}}',
        ):
            show_unknown = st.checkbox(
                f"Show unknown-votes for {result.name}",
                value=False,
                key="vote_unknown_checkbox",
            )

    show_yes_ct = show_no_ct = show_unknown_ct = False
    if compare_to is not None:
        with cols[0]:
            with stylable_container(
                key="yes_button_2",
                css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_YES_2};border-color: {COLOR_YES_2};}}',
            ):
                show_yes_ct = st.checkbox(
                    f"Show yes-votes for {compare_to.name}",
                    value=True,
                    key="vote_yes_checkbox_2",
                )
        with cols[1]:
            with stylable_container(
                key="no_button_2",
                css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_NO_2};border-color: {COLOR_NO_2};}}',
            ):
                show_no_ct = st.checkbox(
                    f"Show no-votes for {compare_to.name}",
                    value=True,
                    key="vote_no_checkbox_2",
                )
        with cols[2]:
            with stylable_container(
                key="unknown_button_2",
                css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_UNKNOWN_2};border-color: {COLOR_UNKNOWN_2};}}',
            ):
                show_unknown_ct = st.checkbox(
                    f"Show unknown-votes for {compare_to.name}",
                    value=False,
                    key="vote_unknown_checkbox_2",
                )

    edge_threshold = st.slider(
        "Vote visualization threshold",
        min_value=1,
        max_value=6,
        value=2,
        step=1,
        key="edge_threshold_slider",
        help="Only show edges with at least this many votes",
    )

    # Quickly verify that all attributes have a uid
    for attr in result.parameters.source_relation.attributes:
        if attr.uid is None:
            st.error(f"Attribute {attr.name} uid is None")
            return
    for attr in result.parameters.target_relation.attributes:
        if attr.uid is None:
            st.error(f"Attribute {attr.name} uid is None")
            return

    # Lookup tables before constructing the graph
    left_attr_lookup: dict[int, Attribute] = {attr.uid: attr for attr in result.parameters.source_relation.attributes}  # type: ignore
    right_attr_lookup: dict[int, Attribute] = {attr.uid: attr for attr in result.parameters.target_relation.attributes}  # type: ignore

    # this will be the order in which attributes are displayed
    left_attr_uids = sorted(left_attr_lookup.keys())
    right_attr_uids = sorted(right_attr_lookup.keys())

    elements: list[dict[str, Any]] = []
    for attr in (
        result.parameters.source_relation.attributes
        + result.parameters.target_relation.attributes
    ):
        elements.append(
            {
                "data": {"id": str(attr.uid), "name": attr.name},
                "style": {"opacity": 1.0 if attr.included else 0.5},
            }
        )

    # Add edges (=votes) to the graph
    elements.extend(
        _create_edge_elements(
            result,
            left_attr_lookup,
            right_attr_lookup,
            show_yes,
            show_no,
            show_unknown,
            COLOR_YES,
            COLOR_NO,
            COLOR_UNKNOWN,
            "result",
            edge_threshold,
        )
    )
    if compare_to is not None:
        elements.extend(
            _create_edge_elements(
                compare_to,
                left_attr_lookup,
                right_attr_lookup,
                show_yes_ct,
                show_no_ct,
                show_unknown_ct,
                COLOR_YES_2,
                COLOR_NO_2,
                COLOR_UNKNOWN_2,
                "compare_to",
                edge_threshold,
            )
        )

    stylesheet = [
        {
            "selector": "node",
            "style": {
                "label": "data(name)",
                "width": 230,
                "height": 40,
                "shape": "rectangle",
                "text-valign": "center",
                "text-halign": "center",
            },
        },
        {
            "selector": "edge",
            "style": {
                "width": "data(weight)",
                "curve-style": "bezier",
                "line-color": "data(color)",
            },
        },
    ]

    # The custom layout force a bipartite graph
    layout = {"name": "fcose", "animationDuration": 0}
    layout["alignmentConstraint"] = {
        "horizontal": [[str(left_attr_uids[0]), str(right_attr_uids[0])]],
        "vertical": [
            [str(uid) for uid in left_attr_uids],
            [str(uid) for uid in right_attr_uids],
        ],
    }
    layout["relativePlacementConstraint"] = [
        {"left": str(left_attr_uids[0]), "right": str(right_attr_uids[0]), "gap": 600}
    ]
    layout["relativePlacementConstraint"] += [
        {"top": str(uid_a), "bottom": str(uid_b), "gap": 80}
        for uid_a, uid_b in zip(left_attr_uids[:-1], left_attr_uids[1:])
    ]
    layout["relativePlacementConstraint"] += [
        {"top": str(uid_a), "bottom": str(uid_b), "gap": 80}
        for uid_a, uid_b in zip(right_attr_uids[:-1], right_attr_uids[1:])
    ]

    max_num_attrs = max(len(left_attr_uids), len(right_attr_uids))
    selected = cytoscape(
        elements,
        stylesheet,
        layout=layout,
        key="graph",
        height=f"{max_num_attrs*70}px",
        user_zooming_enabled=False,
        user_panning_enabled=False,
    )

    # store selected nodes in session state
    mss.selected_attrs = [int(node_id) for node_id in selected["nodes"]]

    selected_source = [
        attr
        for attr in result.parameters.source_relation.attributes
        if attr.uid in mss.selected_attrs
    ]
    selected_target = [
        attr
        for attr in result.parameters.target_relation.attributes
        if attr.uid in mss.selected_attrs
    ]

    # If exactly 1 source and target attribute selected: show more info on this pair
    if len(selected_source) == 1 and len(selected_target) == 1:
        attr_pair = AttributePair(selected_source[0], selected_target[0])
        _voting_details(result, attr_pair, compare_to)
    else:
        st.info(
            "Select an attribute pair in the graph to see voting details for the selected pair"
        )


def _voting_details(
    result: Result, attr_pair: AttributePair, compare_to: Optional[Result] = None
):
    """Display the voting details for a given attribute pair."""
    st.header(
        f"Voting details between `{result.parameters.source_relation.name}.{attr_pair.source.name}` and `{result.parameters.target_relation.name}.{attr_pair.target.name}`"
    )

    if attr_pair not in result.pairs:
        st.error(
            "Selected attribute pair not found in result. This is most likely a bug."
        )
        return

    if compare_to is not None and attr_pair not in compare_to.pairs:
        st.error(
            "Selected attribute pair not found in compare_to. This is most likely a bug."
        )
        return

    if not all((attr_pair.source.included, attr_pair.target.included)):
        excluded_attr = (
            attr_pair.target if attr_pair.source.included else attr_pair.source
        )
        st.markdown(f"The attribute `{excluded_attr.name}` is not included.")
        return

    # Show votes
    num_cols = 1 if compare_to is None else 2
    cols = st.columns(num_cols)
    with cols[0]:
        if compare_to is not None:
            st.subheader(f"Votes for {result.name}")
        votes = result.pairs[attr_pair].votes
        for i, vote in enumerate(votes):
            with st.expander(f"Vote {i+1}: {vote.vote.name}"):
                st.markdown(vote.explanation)
    if compare_to is not None:
        with cols[1]:
            st.subheader(f"Votes for {compare_to.name}")
            votes = compare_to.pairs[attr_pair].votes
            for i, vote in enumerate(votes):
                with st.expander(f"Vote {i+1}: {vote.vote.name}"):
                    st.markdown(vote.explanation)


def _create_edge_elements(
    result: Result,
    left_attr_lookup,
    right_attr_lookup,
    show_yes,
    show_no,
    show_unknown,
    color_yes,
    color_no,
    color_unknown,
    id_prefix: str,
    edge_threshold: int = 0,
) -> list[dict[str, Any]]:
    elements = []
    for pair, result_pair in result.pairs.items():
        source_uid = pair.source.uid
        target_uid = pair.target.uid
        if source_uid not in left_attr_lookup:
            st.error(f"Source uid {source_uid} not found in left_attr_lookup")
            raise ValueError()
        if target_uid not in right_attr_lookup:
            st.error(f"Target uid {target_uid} not found in right_attr_lookup")
            raise ValueError()
        source_name = left_attr_lookup[source_uid].name
        target_name = right_attr_lookup[target_uid].name
        num_yes = len(
            [decision for decision in result_pair.votes if decision.vote == Vote.YES]
        )
        num_no = len(
            [decision for decision in result_pair.votes if decision.vote == Vote.NO]
        )
        num_unknown = len(
            [
                decision
                for decision in result_pair.votes
                if decision.vote == Vote.UNKNOWN
            ]
        )
        if show_yes and num_yes >= edge_threshold:
            elements.append(
                {
                    "data": {
                        "source": str(source_uid),
                        "target": str(target_uid),
                        "id": f"{id_prefix}.{source_name}➞{target_name}-yes",
                        "weight": num_yes,
                        "color": color_yes,
                    },
                    "selectable": False,
                }
            )
        if show_no and num_no >= edge_threshold:
            elements.append(
                {
                    "data": {
                        "source": str(source_uid),
                        "target": str(target_uid),
                        "id": f"{id_prefix}.{source_name}➞{target_name}-no",
                        "weight": num_no,
                        "color": color_no,
                    },
                    "selectable": False,
                }
            )
        if show_unknown and num_unknown >= edge_threshold:
            elements.append(
                {
                    "data": {
                        "source": str(source_uid),
                        "target": str(target_uid),
                        "id": f"{id_prefix}.{source_name}➞{target_name}-unknown",
                        "weight": num_unknown,
                        "color": color_unknown,
                    },
                    "selectable": False,
                }
            )
    return elements


def toy_example():
    # TODO: remove when example no longer needed
    elements = [
        {"data": {"id": "X", "name": "A"}, "selected": True, "selectable": False},
        {"data": {"id": "Y", "name": "B"}},
        {"data": {"id": "Z", "name": "C"}},
        {"data": {"source": "X", "target": "Y", "id": "X➞Y"}},
        {"data": {"source": "Z", "target": "Y", "id": "Z➞Y"}},
        {"data": {"source": "Z", "target": "X", "id": "Z➞X"}},
    ]

    stylesheet = [
        {
            "selector": "node",
            "style": {
                "label": "data(name)",
                "width": 20,
                "height": 20,
                "labelValign": "middle",
                "text-valign": "center",
                "text-halign": "center",
            },
        },
        {
            "selector": "edge",
            "style": {
                "width": 3,
                "curve-style": "bezier",
                "target-arrow-shape": "triangle",
            },
        },
    ]

    layout = {"name": "fcose", "animationDuration": 0}
    # layout["alignmentConstraint"] = {"horizontal": [["X", "Y"]], "vertical" : [["X", "Z"]]}
    layout["relativePlacementConstraint"] = [{"top": "X", "bottom": "Z"}]
    layout["relativePlacementConstraint"] += [{"left": "X", "right": "Y"}]

    selected = cytoscape(elements, stylesheet, layout=layout, key="graph_toy")

    st.markdown("**Selected nodes**: %s" % (", ".join(selected["nodes"])))
    st.markdown("**Selected edges**: %s" % (", ".join(selected["edges"])))

    st.write(elements)
    st.write(layout)
