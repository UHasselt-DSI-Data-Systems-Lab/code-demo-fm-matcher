from .models import Feedback, Parameters, Relation, Result
from .processing import generate_result
from .prompting import generate_prompts
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
    parameters = store_parameters(parameters)
    prompts = generate_prompts(parameters)
    result = generate_result(parameters, prompts)
    result = store_result(result)
    return result
