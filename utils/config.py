import os

default_config = {
    "QUERY_OPENAI": True,  # if set to False, this generates a random result instead of prompting the LLM
    "OPENAI_MODEL": "o3-mini-2025-01-31",  # the default model to use on the OpenAI API
    "OPENAI_MODELS": [
        "gpt-4.1-2025-04-14",
        "o4-mini-2025-04-16",
        "o3-2025-04-16",
        "gpt-4.1-mini-2025-04-14",
        "gpt-4.1-nano-2025-04-14",

    ],  # a list of alternative models choosable in LLM-matcher
    "OPENAI_N": 3,  # the number of answers to generate per prompt
    "OPENAI_TEMPERATURE": 1.0,  # the model temperature to use
    "OPENAI_TIMEOUT": 60,  # the timeout for OpenAI API calls
    "TEMPLATE_DIR": "resources/prompt_templates",  # the directory where prompt templates are stored
    "PARALLEL_OPENAI_REQUESTS": 5,  # the maximum number of parallel requests that will be sent to the OpenAI API (lower this to fix frequent RateLimitErrors)
    "SQLITE_PATH": "dev.sqlite3",  # the path to the SQLite database file. Set this to None to disable storage.
}

config = {
    # use the environment variables if set (typecasted to the type given in default_config), other use default_config values
    k: None if os.getenv(k, v) == "None" else type(default_config[k])(os.getenv(k, v))
    for k, v in default_config.items()
}
