from contextlib import contextmanager
import datetime
import functools
import json
import sqlite3
from typing import List, Optional

from openai.types.chat import ChatCompletion

from .config import config
from .models import Answer, Parameters, Prompt, Result


@contextmanager
def get_connection(db_path: str) -> sqlite3.Connection:
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
                "parameters_id INTEGER NOT NULL REFERENCES parameters (id) ON DELETE CASCADE ON UPDATE CASCADE",
                "name TEXT",
                "datetime INTEGER",
                "hash TEXT NOT NULL",
                "data JSON NOT NULL",
            ],
            "prompts": [
                "id INTEGER PRIMARY KEY",
                "parameters_id INTEGER NOT NULL REFERENCES parameters (id) ON DELETE CASCADE ON UPDATE CASCADE",
                "hash TEXT NOT NULL",
                "data JSON NOT NULL",
            ],
            "chatcompletions": [
                "openai_id TEXT PRIMARY KEY",
                "prompt_id INTEGER NOT NULL REFERENCES prompts (id) ON DELETE CASCADE ON UPDATE CASCADE",
                "data JSON NOT NULL",
            ],
            "answers": [
                "chatcompletions_id TEXT REFERENCES chatcompletions (openai_id) ON DELETE CASCADE ON UPDATE CASCADE",
                "prompt_id INTEGER NOT NULL REFERENCES prompts (id) ON DELETE CASCADE ON UPDATE CASCADE",
                "valid INTEGER NOT NULL",
                "hash TEXT NOT NULL",
                "data JSON NOT NULL",
            ],
        }
        for table, columns in create_stmt.items():
            try:
                con.execute(f"CREATE TABLE {table} ({', '.join(columns)});")
            except sqlite3.Error as err:
                # TODO: do proper logging here
                print(err)
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
    if config["SQLITE_PATH"] is None:
        parameters.meta["path"] = _to_path("nostore", "parameters", "1")
        return parameters
    now = datetime.datetime.now()
    db_path = config["SQLITE_PATH"]
    with get_connection(db_path) as con:
        result = con.execute(
            "INSERT INTO parameters VALUES (?, ?, ?, ?) RETURNING id;",
            (None, now, parameters.digest(), json.dumps(parameters.to_dict())),
        )
        new_id = result.fetchone()[0]
    parameters.meta["path"] = _to_path(db_path, "parameters", new_id)
    return parameters


def store_result(result: Result) -> Result:
    """Stores a result. It will add a path to the Result's meta information that is needed to retrieve the result later."""
    if config["SQLITE_PATH"] is None:
        result.meta["path"] = _to_path("nostore", "results", "1")
        return result
    now = datetime.datetime.now()
    db_path = config["SQLITE_PATH"]
    with get_connection(db_path) as con:
        sql_result = con.execute(
            "INSERT INTO results VALUES (?, ?, ?, ?, ?, ?) RETURNING id;",
            (
                None,
                _id_from_path(result.parameters.meta["path"]),
                "dunno",
                now,
                result.digest(),
                result.to_json(),
            ),
        )
        new_id = sql_result.fetchone()[0]
    result.meta["path"] = _to_path(db_path, "results", new_id)
    return result


def store_prompt(prompt: Prompt) -> Prompt:
    """Stores a prompt. It will add a path to the Prompt's meta information that is needed to retrieve the prompt later."""
    if config["SQLITE_PATH"] is None:
        prompt.meta["path"] = _to_path("nostore", "prompts", "1")
        return prompt
    db_path = config["SQLITE_PATH"]
    with get_connection(db_path) as con:
        result = con.execute(
            "INSERT INTO prompts VALUES (?, ?, ?, ?) RETURNING id;",
            (
                None,
                _id_from_path(prompt.parameters.meta["path"]),
                prompt.digest(),
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
    if config["SQLITE_PATH"] is None:
        return chatcompletion
    db_path = config["SQLITE_PATH"]
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
    if config["SQLITE_PATH"] is None:
        answer.meta["path"] = _to_path("nostore", "answers", "1")
        return answer
    db_path = config["SQLITE_PATH"]
    with get_connection(db_path) as con:
        con.execute(
            "INSERT INTO answers VALUES (?, ?, ?, ?, ?);",
            (
                chatcompletion_id,
                _id_from_path(prompt_path),
                answer.valid,
                answer.digest(),
                json.dumps(answer.to_dict()),
            ),
        )
    return answer


def get_parameters_by_hash(the_hash: str) -> Optional[Parameters]:
    """Returns the parameters with the given hash. If the parameters are not stored, returns None."""
    if config["SQLITE_PATH"] is None:
        return None
    db_path = config["SQLITE_PATH"]
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
    if config["SQLITE_PATH"] is None:
        return None
    db_path = config["SQLITE_PATH"]
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


def get_prompt_by_parameters(parameters: Parameters) -> List[Prompt]:
    """Returns all prompts for the given parameters. Returns an empty list if none are stored."""
    if config["SQLITE_PATH"] is None:
        return []
    db_path = config["SQLITE_PATH"]
    prompts = []
    with get_connection(db_path) as con:
        sql_result = con.execute(
            "SELECT data FROM prompts WHERE parameters_id=?;",
            (_id_from_path(parameters.meta["path"]),)
        ).fetchall()
        prompts = [Prompt.from_dict(json.loads(res[0])) for res in sql_result]
    return prompts


def get_answers_by_prompt(prompt: Prompt, filter_valid: bool = False) -> List[Answer]:
    """Returns all answers for the given prompt. Returns an empty list if none are stored."""
    if config["SQLITE_PATH"] is None:
        return []
    db_path = config["SQLITE_PATH"]
    answers = []
    with get_connection(db_path) as con:
        if filter_valid:
            sql_qry = "SELECT data FROM answers WHERE prompt_id=? AND valid=1;"
        else:
            sql_qry = "SELECT data FROM answers WHERE prompt_id=?;"
        sql_result = con.execute(
            sql_qry, (_id_from_path(prompt.meta["path"]),)
        ).fetchall()
        answers = [Answer.from_dict(json.loads(res[0])) for res in sql_result]
    return answers
