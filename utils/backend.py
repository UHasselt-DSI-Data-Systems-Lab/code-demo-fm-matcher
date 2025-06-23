from typing import List

from .config import config
from .models import Answer, Feedback, Parameters, PromptAttributePair, Relation, Result
from .prompt_sending import send_prompts
from .prompt_building import build_prompts, PromptDesign
from .prompt_postprocessing import postprocess_answers
from .storage import (
    store_parameters,
    store_result,
    get_parameters_by_hash,
    get_result_by_parameters,
    _id_from_path,
)


def get_available_openai_models() -> List[str]:
    if config["OPENAI_MODEL"] in config["OPENAI_MODELS"]:
        config["OPENAI_MODELS"].remove(config["OPENAI_MODEL"])
    return [config["OPENAI_MODEL"]] + config["OPENAI_MODELS"]


def schema_match(
    parameters: Parameters = None,
) -> Result:
    """Perform schema matching on two tables. Either provide a set of parameters or two tables and a feedback object."""
    if parameters is None:
        raise ValueError("You need to provide parameters for this method.")

    stored_params = get_parameters_by_hash(parameters.digest())
    if stored_params is None:
        parameters = store_parameters(parameters)
    else:
        parameters = stored_params
    result = get_result_by_parameters(parameters)
    if result is not None:
        return result
    prompts = build_prompts(
        parameters,
        templates=["oneToN", "nToOne", "nToN"],
        modes=[PromptDesign.oneToN, PromptDesign.nToOne, PromptDesign.nToN],
        model=parameters.llm_model,
    )

    if not config["QUERY_OPENAI"]:
        # method stub
        from .models import AttributePair, Decision, ResultPair, Vote
        import itertools
        import random

        attribute_pairs = [
            AttributePair(
                source=src,
                target=trgt,
            )
            for (src, trgt) in itertools.product(
                parameters.source_relation.attributes,
                parameters.target_relation.attributes,
            )
        ]
        result = Result(
            parameters=parameters,
            pairs={
                ap: ResultPair(
                    ap,
                    votes=[
                        Decision(
                            vote=rs,
                            explanation="Testing",
                            answer=Answer(
                                PromptAttributePair(
                                    [ap.source],
                                    [ap.target],
                                ),
                                "testing",
                                1,
                                True,
                            ),
                        )
                        for rs in random.choices(
                            [Vote.YES, Vote.NO, Vote.UNKNOWN], weights=[1, 5, 2], k=3
                        )
                    ],
                    score=0.0,
                )
                for ap in attribute_pairs
            },
        )
    else:
        answers = send_prompts(parameters, prompts)
        result = postprocess_answers(parameters, answers)
    result.name = (
        f"Exp. {_id_from_path(result.parameters.meta['path'])}: "
        f"{result.parameters.source_relation.name} -> "
        f"{result.parameters.target_relation.name} "
        f"({result.parameters.llm_model}) "
    )
    result = store_result(result)
    return result
