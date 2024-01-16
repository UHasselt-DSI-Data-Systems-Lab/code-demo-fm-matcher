import itertools
from typing import List

from jinja2 import Environment
from openai.types.completion_create_params import CompletionCreateParamsBase

from .models import AttributePair, Parameters


def generate_prompts(parameters: Parameters) -> List[CompletionCreateParamsBase]:
    """Generate OpenAI Chat Completion prompts from parameters."""
    return [
        CompletionCreateParamsBase(
            {
                "model": "gpt-3.5-turbo-1106",
                "prompt": [{"role": "user", "content": "Say Hello!"}],
                "n": 3,
            }
        )
    ]
