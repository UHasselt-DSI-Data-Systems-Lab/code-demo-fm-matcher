from .models import Parameters, Result


def store_parameters(parameters: Parameters) -> Parameters:
    """Stores the parameters. It will add a path to the Parameter's meta information that is needed to retrieve the parameters later."""
    # TODO: implement this properly
    # parameters.save()
    parameters.meta["path"] = "path/to/parameters"
    return parameters


def store_result(result: Result) -> Result:
    """Stores a result. It will add a path to the Result's meta information that is needed to retrieve the result later."""
    # TODO: implement this properly
    # result.save()
    result.meta["path"] = "path/to/result"
    return result


def read_parameters(path: str) -> Parameters:
    """Reads parameters from a path."""
    raise NotImplementedError("Without saving there is no reading.")


def read_result(path: str) -> Result:
    raise NotImplementedError("Without saving there is no reading.")
