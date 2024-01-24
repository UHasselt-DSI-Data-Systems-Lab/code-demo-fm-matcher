config = {
    "DEBUG_MODE": True,
    "OPENAI_MODEL": "gpt-3.5-turbo-1106",  # the model to use on the OpenAI API
    "OPENAI_N": 3,  # the number of answers to generate per prompt
    "OPENAI_TEMPERATURE": 1.0,  # the model temperature to use
    "PARALLEL_OPENAI_REQUESTS": 5,  # the maximum number of parallel requests that will be sent to the OpenAI API (lower this to fix frequent RateLimitErrors)
    "SQLITE_PATH": "database.sqlite3",  # the path to the SQLite database file
}
