import asyncio
import copy
import json
from typing import Any, Dict, List

from openai import AsyncOpenAI, APITimeoutError, InternalServerError, RateLimitError
from openai.types.chat import ChatCompletion, CompletionCreateParams
import tenacity

from .config import config
from .errors import NotDoneException
from .models import Answer, Parameters, Prompt
from .storage import store_answer, store_chatcompletion, get_answers_by_prompt


def send_prompts(parameters: Parameters, prompts: List[Prompt]) -> List[Answer]:
    """Generate a result from parameters and prompts."""
    return asyncio.run(process_prompt_list(parameters, prompts))


@tenacity.retry(
    stop=tenacity.stop_after_attempt(3),
    wait=tenacity.wait_random(
        min=15, max=45
    ),  # this is mainly included to allow calming RateLimitErrors
    retry=(
        tenacity.retry_if_exception_type(APITimeoutError)
        | tenacity.retry_if_exception_type(RateLimitError)
        | tenacity.retry_if_exception_type(InternalServerError)
    ),
)
async def ask_gpt(params: CompletionCreateParams) -> ChatCompletion:
    """Perform a reqeust using the OpenAI Python SDK. The method itself is a very thin wrapper and is mainly used to use retrying using tenacity."""
    client = AsyncOpenAI()
    return await client.chat.completions.create(**params)


def result_into_answers(result: ChatCompletion, prompt: Prompt) -> List[Answer]:
    return [
        Answer(
            prompt.attributes,
            index=choice.index,
            answer=choice.message.content,
        )
        for choice in result.choices
    ]


async def process_and_store_prompt(
    parameters: Parameters,
    prompt: Prompt,
    semaphore: asyncio.Semaphore = asyncio.Semaphore(1),
) -> List[Answer]:
    """Process a prompt and store the result. This method features a semaphore to avoid running into RateLimitErrors. Return the Answers in a list."""
    valid_answers = get_answers_by_prompt(prompt, filter_valid=True)
    _completion_prompt = copy.deepcopy(prompt.prompt)
    _completion_prompt["n"] -= len(valid_answers)
    if _completion_prompt["n"] > 0:
        try:
            for attempt in tenacity.Retrying(
                stop=tenacity.stop_after_attempt(5),
                retry=(tenacity.retry_if_exception_type(NotDoneException)),
            ):
                with attempt:
                    async with semaphore:
                        result = await ask_gpt(_completion_prompt)
                    # TODO: evaluate the choice to check the answers validity here
                    store_chatcompletion(result, prompt.meta["path"])
                    answers = result_into_answers(result, prompt)
                    for answer in answers:
                        if is_valid_answer(answer):
                            _completion_prompt["n"] -= 1
                            answer.valid = True
                            valid_answers.append(answer)
                        store_answer(answer, prompt.meta["path"], result.id)
                    if _completion_prompt["n"] > 0:
                        raise NotDoneException("Not enough valid answers provided.")
        except tenacity.RetryError:
            pass
    # NOTE: I am restricting the return to OPENAI_N elements here, unsure whether this will be really necessary though
    return valid_answers[0:config["OPENAI_N"]]


async def process_prompt_list(
    parameters: Parameters, prompts: List[Prompt]
) -> List[Answer]:
    """Process a list of prompts. Returns the chained lists of all answers provided from the LLM."""
    semaphore = asyncio.Semaphore(config["PARALLEL_OPENAI_REQUESTS"])
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for prompt in prompts:
            tasks.append(
                tg.create_task(process_and_store_prompt(parameters, prompt, semaphore))
            )
    return [result for task in tasks for result in task.result()]


def extract_json(answer: Answer) -> Dict[str, Any]:
    """Extract the JSON formatted summary from an Answer retrieved from GPT."""
    # checks whether there is a proper JSON structure in the response
    start_decision = answer.answer.rindex("{")
    end_decision = answer.answer.index("}", start_decision)
    # cleanup step
    raw_json = answer.answer[start_decision : end_decision + 1].replace("'", '"')
    return json.loads(raw_json)


def is_valid_answer(answer: Answer) -> bool:
    """Check whether an Answer is valid."""
    try:
        extract_json(answer)
    except:  # noqa: E722
        return False
    return True
