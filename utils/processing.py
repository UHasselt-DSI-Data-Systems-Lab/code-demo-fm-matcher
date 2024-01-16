import itertools
from typing import List

from openai.types.completion_create_params import CompletionCreateParamsBase

from .models import AttributePair, Decision, Parameters, Result, ResultPair, Vote


def generate_result(
    parameters: Parameters, prompts: List[CompletionCreateParamsBase]
) -> Result:
    """Generate a result from parameters and prompts."""
    attribute_pairs = [
        AttributePair(s, t)
        for s, t in itertools.product(
            parameters.source_relation.attributes,
            parameters.target_relation.attributes,
        )
    ]
    return Result(
        name="test",
        parameters=parameters,
        pairs={
            ap: ResultPair(
                ap,
                votes=[
                    Decision(vote=Vote.NO, explanation="Testing"),
                    Decision(vote=Vote.NO, explanation="Testing"),
                    Decision(vote=Vote.NO, explanation="Testing"),
                ],
                score=0.0,
            )
            for ap in attribute_pairs
        },
    )
