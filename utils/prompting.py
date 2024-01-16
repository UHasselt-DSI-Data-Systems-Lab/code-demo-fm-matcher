from collections.abc import Iterable
import functools
import json
import os
from typing import Any, Dict, List, Tuple

from jinja2 import Environment
from openai.types.completion_create_params import CompletionCreateParamsBase

from .models import Attribute, Parameters


def generate_prompts(parameters: Parameters) -> List[CompletionCreateParamsBase]:
    """Generate OpenAI Chat Completion prompts from parameters."""
    prompt_oneToN = [
        (s, parameters.target_relation.attributes)
        for s in parameters.source_relation.attributes
    ]
    rendered_oneToN = [render_prompt(p, parameters, "oneToN") for p in prompt_oneToN]

    # prompt_NtoOne = [
    #    (parameters.source_relation.attributes, t)
    #    for t in parameters.target_relation.attributes
    # ]

    return [
        CompletionCreateParamsBase(
            {
                "model": "gpt-3.5-turbo-1106",
                "prompt": rendered_oneToN,
                "n": 3,
            }
        )
    ]


@functools.cache
def read_prompt_template(template: str) -> List[Dict[str, str]]:
    """Read a prompt template from a file."""
    with open(os.path.join("resources", f"prompt_template_{template}.json"), "r") as f:
        tpl = json.load(f)
    return tpl


def template_iterator(
    template: List[Dict[str, str]],
    sources: List[Attribute],
    targets: List[Attribute],
) -> Iterable:
    """An iterator that allows to detect which parts of a prompt template need to be repeated in order to facilitate 1-to-N, N-to-1 or N-to-N prompt templates."""
    for part in template:
        if "{{source_attribute.name}}" in part["content"]:
            for s in sources:
                yield part, s, targets[0]
        elif "{{target_attribute.name}}" in part["content"]:
            for t in targets:
                yield part, sources[0], t
        else:
            yield part, sources[0], targets[0]


def render_prompt(
    prompt_data: Tuple[Any, Any], parameters: Parameters, template: str
) -> List[Dict[str, str]]:
    """Render a single prompt from a tuple of source and target attributes."""
    sources = prompt_data[0]
    if not isinstance(sources, list):
        sources = [sources]
    targets = prompt_data[1]
    if not isinstance(targets, list):
        targets = [targets]
    template = read_prompt_template(template)
    env = Environment()
    return [
        {
            "role": p["role"],
            "content": env.from_string(p["content"]).render(
                **{
                    "source_relation": parameters.source_relation,
                    "source_attribute": s,
                    "target_relation": parameters.target_relation,
                    "target_attribute": t,
                    # TODO: what about feedback?
                }
            ),
        }
        for p, s, t in template_iterator(template, sources, targets)
    ]
