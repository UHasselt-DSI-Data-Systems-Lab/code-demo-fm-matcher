# LLM-Matcher

LLM-Matcher demonstrates the use of Large Language Models for Schema Matching. Find more information [in our publication](https://arxiv.org/abs/2407.11852). This tool uses the [OpenAI Python SDK](https://github.com/openai/openai-python) to communicate with the OpenAI API. Other models are currently not supported out-of-the-box.

## Installation

We use (and thus recommend) to install LLM-Matcher using [poetry](https://python-poetry.org/):

```sh
poetry install
```

You may also choose to inspect the `requirements.txt` file to install the tool manually via `pip`.

### Container usage

You may also choose to use LLM-Matcher containerized. We provide a `Dockerfile` in this repository, based on a Python slim image. You can build an image with podman, for example, like this:

```sh
podman build -t fm_matcher .
```

## Configuration

Under Linux and in the containerized setting, you can use environment variables to configure LLM-Matcher. Other OSes are not tested, but you can change the default configuration in `utils/config.py` if needed.

* `OPENAI_API_KEY`: **REQUIRED** The OpenAI API key that will be used. There is no default, you will have to [create an OpenAI API key yourself](https://platform.openai.com/docs/quickstart).
* `QUERY_OPENAI`: Set this to False to generate a random result instead of prompting the LLM. Useful for testing and developing. Default: `True`
* `OPENAI_MODEL`: The OpenAI model that is used. Default: `gpt-4o-mini-2024-07-18`
* `OPENAI_N`: The number of answers that is requested from a model per prompt. Default: `3`
* `OPENAI_TEMPERATURE`: The models [temperature setting](https://platform.openai.com/docs/api-reference/assistants/createAssistant#assistants-createassistant-temperature). Default: `1.0`
* `OPENAI_TIMEOUT`: Timeout of the OpenAI API calls. There is some tenacity used to query the API, we would still recommend to test before setting this significantly lower. Default: `60`
* `TEMPLATE_DIR`: Directory where the prompt templates are stored. The template are filled with the schema information from LLM-Matcher and sent to OpenAI. Default: `resources/prompt_templates`
* `PARALLEL_OPENAI_REQUESTS`: Maximum number of parallel requests that will be sent asynchronously to OpenAI. Lower this to fix [RateLimitErrors](https://help.openai.com/en/articles/6891753-what-are-the-best-practices-for-managing-my-rate-limits-in-the-api). `5`
* `SQLITE_PATH`: Path to an SQLite database file, used for caching results. You may set this to `""` to disable. Default: `dev.sqlite3`

## Running

Run LLM-Matcher as you would [run any Streamlit application](https://docs.streamlit.io/get-started/fundamentals/main-concepts): 

```sh
poetry run streamlit run main.py
```

### Container usage

Assuming you have build the container as shown above, you can start a container like this:

```sh
podman run -d --name fm_matcher -e OPENAI_API_KEY="mySuperSecretApiKey" -p 8501:8501 fm_matcher
```
