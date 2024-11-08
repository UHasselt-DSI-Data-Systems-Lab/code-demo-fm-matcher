import itertools
from typing import List

from .models import (
    Answer,
    AttributePair,
    Decision,
    Parameters,
    Result,
    ResultPair,
    Vote,
)
from .prompt_sending import extract_json


def postprocess_answers(parameters: Parameters, answers: List[Answer]) -> Result:
    """Postprocess all answers into structured Results. At this point, we will assume that the answers are validated."""
    result = _generate_empty_result(parameters)
    for answer in answers:
        reversed_json = {
            str(attribute): decision
            for decision, attribute_list in extract_json(answer).items()
            for attribute in attribute_list
        }
        for src, trgt in itertools.product(
            answer.attributes.sources,
            answer.attributes.targets,
        ):
            if len(answer.attributes.sources) == len(answer.attributes.targets) == 1:
                # by convention, I use the target attribute name for 1 to 1
                look_for = trgt.name
            elif len(answer.attributes.sources) == 1:
                look_for = trgt.name
            elif len(answer.attributes.targets) == 1:
                look_for = src.name
            else:
                look_for = f"{src.name},{trgt.name}"
            if look_for in reversed_json:
                try:
                    vote = Vote[reversed_json[look_for].upper()]
                except KeyError:
                    # the JSON is malformed at this point.
                    vote = Vote.UNKNOWN
            else:
                vote = Vote.UNKNOWN
            result_pair = result.pairs[AttributePair(src, trgt)]
            decision = Decision(vote=vote, explanation=answer.answer, answer=answer)
            result_pair.votes.append(decision)
    return result


def _generate_empty_result(parameters: Parameters) -> Result:
    """Helper method that generates an empty, yet structured (i.e. filled with all attribute combinations) Result object."""
    attribute_combinations = list(
        itertools.product(
            parameters.source_relation.attributes, parameters.target_relation.attributes
        )
    )
    return Result(
        name="test",
        parameters=parameters,
        pairs={
            AttributePair(src, trgt): ResultPair(attributes=AttributePair(src, trgt))
            for (src, trgt) in attribute_combinations
        },
    )
