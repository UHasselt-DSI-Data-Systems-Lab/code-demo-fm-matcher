import streamlit as st
from st_cytoscape import cytoscape
from streamlit_extras.stylable_container import stylable_container
from utils.model_session_state import ModelSessionState
from utils.models import Attribute, Vote

COLOR_YES = "#4bff4b"
COLOR_NO = "#ff4b4b"
COLOR_UNKNOWN = "#bfbfbf"

def create_visualize_screen(mss: ModelSessionState):
    st.header("Results")

    if mss.result is None:
        st.warning("No results to visualize yet")
        return

    # Selectors for visualized vote types
    #st.write("Show votes:")
    cols = st.columns(6)
    with cols[0]:
        with stylable_container(
            key="yes_button",
            css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_YES};border-color: {COLOR_YES};}}',
        ):
            show_yes = st.checkbox("Show yes-votes", value=True, key="vote_yes_checkbox")
    with cols[1]:
        with stylable_container(
            key="no_button",
            css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_NO};border-color: {COLOR_NO};}}',
        ):
            show_no = st.checkbox("Show no-votes", value=True, key="vote_no_checkbox")
    with cols[2]:
        with stylable_container(
            key="unknown_button",
            css_styles=f'span:has(+ input[aria-checked="true"]) {{background-color: {COLOR_UNKNOWN};border-color: {COLOR_UNKNOWN};}}',
        ):
            show_unknown = st.checkbox("Show unknown-votes", value=True, key="vote_unknown_checkbox")

    result = mss.result

    # Quickly verify that all attributes have a uid
    for attr in result.parameters.source_relation.attributes:
        if attr.uid is None:
            st.error(f"Attribute {attr.name} uid is None")
            return
    for attr in result.parameters.target_relation.attributes:
        if attr.uid is None:
            st.error(f"Attribute  {attr.name} uid is None")
            return

    # Lookup tables before constructing the graph
    left_attr_lookup: dict[int, Attribute] = {attr.uid: attr for attr in result.parameters.source_relation.attributes} #type: ignore
    right_attr_lookup: dict[int, Attribute] = {attr.uid: attr for attr in result.parameters.target_relation.attributes} #type: ignore

    # this will be the order in which attributes are displayed
    left_attr_uids = sorted(left_attr_lookup.keys())
    right_attr_uids = sorted(right_attr_lookup.keys())

    elements = [
        {"data": {"id": str(attr.uid), "name": attr.name}}
        for attr in result.parameters.source_relation.attributes
    ]
    elements += [
        {"data": {"id": str(attr.uid), "name": attr.name}}
        for attr in result.parameters.target_relation.attributes
    ]

    # Add edges (=votes) to the graph
    for pair, result_pair in result.pairs.items():
        source_uid = pair.source.uid
        target_uid = pair.target.uid
        if source_uid not in left_attr_lookup:
            st.error(f"Source uid {source_uid} not found in left_attr_lookup")
            return
        if target_uid not in right_attr_lookup:
            st.error(f"Target uid {target_uid} not found in right_attr_lookup")
            return
        source_name = left_attr_lookup[source_uid].name
        target_name = right_attr_lookup[target_uid].name
        num_yes = len([decision for decision in result_pair.votes if decision.vote == Vote.YES])
        num_no = len([decision for decision in result_pair.votes if decision.vote == Vote.NO])
        num_unknown = len([decision for decision in result_pair.votes if decision.vote == Vote.UNKNOWN])
        num_yes += 1
        num_unknown += 1
        if show_yes:
            elements.append(
                {
                    "data": {
                        "source": str(source_uid),
                        "target": str(target_uid),
                        "id": f"{source_name}➞{target_name}-yes",
                        "weight": num_yes,
                        "color": COLOR_YES
                    },
                    "selectable": False,
                }
            )
        if show_no:
            elements.append(
                {
                    "data": {
                        "source": str(source_uid),
                        "target": str(target_uid),
                        "id": f"{source_name}➞{target_name}-no",
                        "weight": num_no,
                        "color": COLOR_NO
                    },
                    "selectable": False,
                }
            )
        if show_unknown:
            elements.append(
                {
                    "data": {
                        "source": str(source_uid),
                        "target": str(target_uid),
                        "id": f"{source_name}➞{target_name}-unknown",
                        "weight": num_unknown,
                        "color": COLOR_UNKNOWN
                    },
                    "selectable": False,
                }
            )



    stylesheet = [
        {
            "selector": "node",
            "style": {
                "label": "data(name)",
                "width": 200,
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
        "horizontal": [
                [str(left_attr_uids[0]), str(right_attr_uids[0])]
            ],
        "vertical" : [
                [str(uid) for uid in left_attr_uids],
                [str(uid) for uid in right_attr_uids]
            ]
    }
    layout["relativePlacementConstraint"] = [{"left": str(left_attr_uids[0]), "right": str(right_attr_uids[0]), "gap":600}]
    layout["relativePlacementConstraint"] += [
         {"top": str(uid_a), "bottom": str(uid_b), "gap": 80} for uid_a, uid_b in zip(left_attr_uids[:-1], left_attr_uids[1:])
    ]
    layout["relativePlacementConstraint"] += [
            {"top": str(uid_a), "bottom": str(uid_b), "gap": 80} for uid_a, uid_b in zip(right_attr_uids[:-1], right_attr_uids[1:])
    ]

    max_num_attrs = max(len(left_attr_uids), len(right_attr_uids))
    selected = cytoscape(elements, stylesheet, layout=layout, key="graph", height=f"{max_num_attrs*70}px", user_zooming_enabled=False, user_panning_enabled=False)

    # store selected nodes in session state
    mss.selected_attrs = [int(node_id) for node_id in selected["nodes"]]

    st.write(selected)


def toy_example():
    #TODO: remove when example no longer needed
    elements = [
        {"data": {"id": "X", "name": "A"}, "selected": True, "selectable": False},
        {"data": {"id": "Y", "name": "B"}},
        {"data": {"id": "Z", "name": "C"}},
        {"data": {"source": "X", "target": "Y", "id": "X➞Y"}},
        {"data": {"source": "Z", "target": "Y", "id": "Z➞Y"}},
        {"data": {"source": "Z", "target": "X", "id": "Z➞X"}},
    ]

    stylesheet = [
        {"selector": "node", "style": {"label": "data(name)", "width": 20, "height": 20, "labelValign": "middle", "text-valign" : "center",
        "text-halign" : "center"}},
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
    #layout["alignmentConstraint"] = {"horizontal": [["X", "Y"]], "vertical" : [["X", "Z"]]}
    layout["relativePlacementConstraint"] = [{"top": "X", "bottom": "Z"}]
    layout["relativePlacementConstraint"] += [{"left": "X", "right": "Y"}]

    selected = cytoscape(elements, stylesheet, layout=layout, key="graph_toy")

    st.markdown("**Selected nodes**: %s" % (", ".join(selected["nodes"])))
    st.markdown("**Selected edges**: %s" % (", ".join(selected["edges"])))

    st.write(elements)
    st.write(layout)

    