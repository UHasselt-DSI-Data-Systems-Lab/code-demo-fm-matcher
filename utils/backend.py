from .models import Feedback, Parameters, Relation, Result
from .prompt_sending import send_prompts
from .prompt_building import build_prompts
from .prompt_postprocessing import postprocess_answers
from .storage import store_parameters, store_result


def schema_match(
    parameters: Parameters = None,
    source_relation: Relation = None,
    target_relation: Relation = None,
    feedback: Feedback = None,
) -> Result:
    """Perform schema matching on two tables. Either provide a set of parameters or two tables and a feedback object."""
    if parameters is None:
        if source_relation is None or target_relation is None or feedback is None:
            raise ValueError(
                "Either provide parameters or source and target relation and feedback object."
            )
        else:
            parameters = Parameters(
                source_relation=source_relation,
                target_relation=target_relation,
                feedback=feedback,
            )
    # method stub
    from .models import AttributePair, Decision, ResultPair, Vote
    import itertools
    # comment by Marcel: the part below is now fully functional for basic types of requests
    # parameters = store_parameters(parameters)
    # prompts = build_prompts(parameters)
    # answers = send_prompts(parameters, prompts)
    # result = postprocess_answers(answers, parameters)
    # result = store_result(result)
    # return result

    attribute_pairs = [
        AttributePair(
            source=src,
            target=trgt,
        ) for (src, trgt) in itertools.product(parameters.source_relation.attributes, parameters.target_relation.attributes)
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