import os

default_config = {
    "QUERY_OPENAI": True,  # if set to True, this generates a random result instead of prompting the LLM
    "OPENAI_MODEL": "gpt-3.5-turbo-1106",  # the model to use on the OpenAI API
    "OPENAI_N": 3,  # the number of answers to generate per prompt
    "OPENAI_TEMPERATURE": 1.0,  # the model temperature to use
    "OPENAI_TIMEOUT": 60,  # the timeout for OpenAI API calls
    "PARALLEL_OPENAI_REQUESTS": 5,  # the maximum number of parallel requests that will be sent to the OpenAI API (lower this to fix frequent RateLimitErrors)
    "SQLITE_PATH": "dev.sqlite3",  # the path to the SQLite database file. Set this to None to disable storage.
}

config = {
    # use the environment variables if set (typecasted to the type given in default_config), other use default_config values
    k: type(default_config[k])(os.getenv(k, v))
    for k, v in default_config.items()
}
