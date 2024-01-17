import asyncio
import itertools
from typing import List

from openai import AsyncOpenAI, APITimeoutError, InternalServerError, RateLimitError
from openai.types.chat import ChatCompletion, CompletionCreateParams
import tenacity

from .models import Answer, Parameters, Prompt


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


async def process_and_store_prompt(
    parameters: Parameters,
    prompt: Prompt,
    semaphore: asyncio.Semaphore = asyncio.Semaphore(1),
) -> List[Answer]:
    """Process a prompt and store the result. This method features a semaphore to avoid running into RateLimitErrors. Return the Answers in a list."""
    # TODO: ask if stored
    async with semaphore:
        result = await ask_gpt(prompt.prompt)
    # TODO: store result
    # TODO: a logging entry here would make sense
    return [
        Answer(
            prompt.attributes,
            answer=choice.message.content,
        )
        for choice in result.choices
    ]


async def process_prompt_list(
    parameters: Parameters, prompts: List[Prompt]
) -> List[Answer]:
    """Process a list of prompts. Returns the chained lists of all answers provided from the LLM."""
    semaphore = asyncio.Semaphore(5)  # TODO: get this from the settings
    tasks = []
    async with asyncio.TaskGroup() as tg:
        for prompt in prompts:
            tasks.append(
                tg.create_task(process_and_store_prompt(parameters, prompt, semaphore))
            )
    # TODO: there is no result in this! resolve!
    print([t.result() for t in itertools.chain(*tasks)])
    return [t.result() for t in itertools.chain(*tasks)]
