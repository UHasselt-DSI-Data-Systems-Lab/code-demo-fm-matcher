from contextlib import contextmanager
import datetime
import functools
import json
import sqlite3
from typing import Optional

from openai.types.chat import ChatCompletion

from .models import Answer, Parameters, Prompt, Result


@contextmanager
def get_connection(db_path: str = "database.sqlite3") -> sqlite3.Connection:
    """Returns a connection to the database, making sure that the database is created first. The connections is cached to avoid multiple checks."""
    if not _initialize_database(db_path):
        raise RuntimeError("The database could not be initialized.")
    con = sqlite3.connect(db_path)
    try:
        yield con
    except sqlite3.Error as e:
        # TODO: do some proper logging here
        print(e)
        pass
    finally:
        con.commit()
        con.close()


def _is_initialized(db_path: str) -> bool:
    """Check if the database has been created properly."""
    con = sqlite3.connect(db_path)
    with con:
        result = con.execute(
            (
                "SELECT name "
                "FROM sqlite_schema "
                "WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%';"
            )
        )
    tables = result.fetchall()
    con.close()
    for table in ["parameters", "results", "chatcompletions"]:
        if (table,) not in tables:
            return False
    return True


@functools.lru_cache(maxsize=1)
def _initialize_database(db_path: str) -> bool:
    """Initializes an SQLite3 database to store parameters, results and ChatCompletions."""
    if _is_initialized(db_path):
        return True
    con = sqlite3.connect(db_path)
    with con:
        create_stmt = {
            "parameters": [
                "id INTEGER PRIMARY KEY",
                "datetime INTEGER",
                "hash TEXT NOT NULL",
                "data JSON NOT NULL",
            ],
            "results": [
                "id INTEGER PRIMARY KEY",
                "parameters_id INTEGER NOT NULL REFERENCES parameters (id)",
                "name TEXT",
                "datetime INTEGER",
                "hash TEXT NOT NULL",
                "data JSON NOT NULL",
            ],
            "prompts": [
                "id INTEGER PRIMARY KEY",
                "parameters_id INTEGER NOT NULL REFERENCES parameters (id)",
                "hash TEXT NOT NULL",
                "data JSON NOT NULL",
            ],
            "chatcompletions": [
                "openai_id TEXT PRIMARY KEY",
                "prompt_id INTEGER NOT NULL REFERENCES prompts (id)",
                "data JSON NOT NULL",
            ],
            "answers": [
                "chatcompletions_id TEXT REFERENCES chatcompletions (openai_id)",
                "prompt_id INTEGER NOT NULL REFERENCES prompts (id)",
                "answer TEXT NOT NULL",
                "valid INTEGER NOT NULL",
            ],
        }
        for table, columns in create_stmt.items():
            con.execute(f"CREATE TABLE {table} ({', '.join(columns)});")
    con.close()
    return True


def _to_path(db_path: str, table: str, the_id: int) -> str:
    """Converts a database path to a path that can be used to retrieve the data."""
    return f"{db_path}/{table}/{the_id}"


def _id_from_path(path: str) -> int:
    """Extracts the id from a path."""
    return int(path.split("/")[-1])


def store_parameters(parameters: Parameters) -> Parameters:
    """Stores the parameters. It will add a path to the Parameter's meta information that is needed to retrieve the parameters later."""
    now = datetime.datetime.now()
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        result = con.execute(
            "INSERT INTO parameters VALUES (?, ?, ?, ?) RETURNING id;",
            (None, now, hash(parameters), json.dumps(parameters.to_dict())),
        )
        new_id = result.fetchone()[0]
    parameters.meta["path"] = _to_path(db_path, "parameters", new_id)
    return parameters


def store_result(result: Result) -> Result:
    """Stores a result. It will add a path to the Result's meta information that is needed to retrieve the result later."""
    now = datetime.datetime.now()
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        sql_result = con.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?) RETURNING id;",
            (
                None,
                _id_from_path(result.parameters.meta["path"]),
                "dunno",
                now,
                hash(result),
                result.to_json(),
            ),
        )
        new_id = sql_result.fetchone()[0]
    result.meta["path"] = _to_path(db_path, "results", new_id)
    return result


def store_prompt(prompt: Prompt) -> Prompt:
    """Stores a prompt. It will add a path to the Prompt's meta information that is needed to retrieve the prompt later."""
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        result = con.execute(
            "INSERT INTO prompts VALUES (?, ?, ?, ?) RETURNING id;",
            (
                None,
                _id_from_path(prompt.parameters.meta["path"]),
                hash(prompt),
                json.dumps(prompt.to_dict()),
            ),
        )
        new_id = result.fetchone()[0]
    prompt.meta["path"] = _to_path(db_path, "prompts", new_id)
    return prompt


def store_chatcompletion(
    chatcompletion: ChatCompletion, prompt_path: str
) -> ChatCompletion:
    """Stores a ChatCompletion as received from the OpenAI API."""
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        con.execute(
            "INSERT INTO chatcompletions VALUES (?, ?, ?);",
            (
                chatcompletion.id,
                _id_from_path(prompt_path),
                chatcompletion.model_dump_json(),  # remember that ChatCompletion is a pydantic object
            ),
        )
    return chatcompletion


def store_answer(
    answer: Answer, prompt_path: str, chatcompletion_id: Optional[str]
) -> Answer:
    """Stores an answer. It will add a path to the Answer's meta information that is needed to retrieve the answer later."""
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        con.execute(
            "INSERT INTO answers VALUES (?, ?, ?, ?);",
            (
                chatcompletion_id,
                _id_from_path(prompt_path),
                answer.answer,
                answer.valid,
            ),
        )
    return answer


def get_parameters_by_hash(the_hash: str) -> Optional[Parameters]:
    """Returns the parameters with the given hash. If the parameters are not stored, returns None."""
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        result = con.execute(
            "SELECT id, datetime, data FROM parameters WHERE hash=?;", (the_hash,)
        ).fetchone()
        if result is None:
            return None
        parameters = Parameters.from_dict(json.loads(result[2]))
        parameters.meta["path"] = _to_path(db_path, "parameters", result[0])
    return parameters


def get_result_by_parameters(parameters: Parameters) -> Optional[Result]:
    """Returns the result for the given parameters. If the result is not stored, returns None."""
    db_path = "database.sqlite3"  # TODO: get this from settings somehow
    with get_connection(db_path) as con:
        sql_result = con.execute(
            "SELECT id, datetime, data FROM results WHERE parameters_id=?;",
            (_id_from_path(parameters.meta["path"]),),
        ).fetchone()
        if sql_result is None:
            return None
        result = Result.from_json(sql_result[2])
        result.meta["path"] = _to_path(db_path, "results", sql_result[0])
    return result
