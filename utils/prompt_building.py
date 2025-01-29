from collections.abc import Iterable
from enum import StrEnum
import functools
import json
import os
from typing import Any, Dict, List, Tuple, Union

from jinja2 import Environment
from openai.types.chat.completion_create_params import (
    CompletionCreateParamsNonStreaming,
)

from .config import config
from .models import Attribute, Parameters, Prompt, PromptAttributePair
from .storage import store_prompt


class PromptDesign(StrEnum):
    """An enum of prompt designs."""

    oneToOne = "1-1"
    oneToN = "1-n"
    nToOne = "n-1"
    nToN = "n-n"


def build_prompts(
    parameters: Parameters,
    templates: List[str] = ["oneToN", "nToOne"],
    modes: List[PromptDesign] = [PromptDesign.oneToN, PromptDesign.nToOne],
    model: str = config["OPENAI_MODEL"],
) -> List[Prompt]:
    """Generate OpenAI Chat Completion prompts from parameters."""
    rendered = []
    if model is None:
        model = config["OPENAI_MODEL"],
    for template, mode in zip(templates, modes):
        source_card, target_card = mode.split("-")
        sources = [
            attr for attr in parameters.source_relation.attributes if attr.included
        ]
        if source_card == "n":
            sources = [sources]

        targets = [
            attr for attr in parameters.target_relation.attributes if attr.included
        ]
        if target_card == "n":
            targets = [targets]

        for source in sources:
            for target in targets:
                rendered.append(
                    Prompt(
                        parameters=parameters,
                        attributes=PromptAttributePair(
                            source if source_card == "n" else [source],
                            target if target_card == "n" else [target],
                        ),
                        prompt=CompletionCreateParamsNonStreaming(
                            {
                                "model": model,
                                "temperature": config["OPENAI_TEMPERATURE"],
                                "messages": render_prompt(
                                    (source, target),
                                    parameters,
                                    template,
                                ),
                                "n": config["OPENAI_N"],
                                "timeout": config["OPENAI_TIMEOUT"],
                            }
                        ),
                    )
                )

    rendered = [store_prompt(prompt) for prompt in rendered]
    return rendered


@functools.cache
def read_prompt_template(template: str) -> List[Dict[str, str]]:
    """Read a prompt template from a file."""
    with open(os.path.join(config["TEMPLATE_DIR"], f"{template}.json"), "r") as f:
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
    prompt_data: Tuple[
        Union[List[Attribute], Attribute], Union[List[Attribute], Attribute]
    ],
    parameters: Parameters,
    template: str,
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
