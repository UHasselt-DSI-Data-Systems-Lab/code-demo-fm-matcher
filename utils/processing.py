import asyncio
from typing import List

from .models import AttributePair, Decision, Parameters, Prompt, Result, ResultPair, Vote


def generate_result(
    parameters: Parameters, prompts: List[Prompt]
) -> Result:
    """Generate a result from parameters and prompts."""
    # TODO: implement this from here on
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
