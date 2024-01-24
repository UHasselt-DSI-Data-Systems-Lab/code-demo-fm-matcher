from collections.abc import Iterable
import functools
import json
import os
from typing import Any, Dict, List, Tuple

from jinja2 import Environment
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsNonStreaming,
)

from .config import config
from .models import Attribute, Parameters, Prompt, PromptAttributePair
from .storage import store_prompt


def build_prompts(parameters: Parameters) -> List[Prompt]:
    """Generate OpenAI Chat Completion prompts from parameters."""
    rendered_oneToN = [
        Prompt(
            parameters=parameters,
            attributes=PromptAttributePair(
                [source_attribute],
                parameters.target_relation.attributes
            ),
            prompt=CompletionCreateParamsNonStreaming(
                {
                    "model": config["OPENAI_MODEL"],
                    "temperature": config["OPENAI_TEMPERATURE"],
                    "messages": render_prompt(
                        (source_attribute, parameters.target_relation.attributes),
                        parameters,
                        "oneToN",
                    ),
                    "n": config["OPENAI_N"],
                    "timeout": config["OPENAI_TIMEOUT"],
                }
            ),
        )
        for source_attribute in parameters.source_relation.attributes
    ]
    rendered_oneToN = [store_prompt(p) for p in rendered_oneToN]

    # prompt_NtoOne = [
    #    (parameters.source_relation.attributes, t)
    #    for t in parameters.target_relation.attributes
    # ]

    return rendered_oneToN


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
    messages = [
        {
            "role": part["role"],
            "content": env.from_string(part["content"]).render(
                **{
                    "source_relation": parameters.source_relation,
                    "source_attribute": source,
                    "target_relation": parameters.target_relation,
                    "target_attribute": target,
                    "feedback": parameters.feedback,
                }
            ),
        }
        for part, source, target in template_iterator(template, sources, targets)
    ]
    return [m for m in messages if len(m["content"]) > 0]
