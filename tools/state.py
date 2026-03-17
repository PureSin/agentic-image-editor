"""Module-level state shared across all tool calls within a single run."""

_working_path: str = ""
_trace: list[dict] = []
_current_iteration: int = 1


def set_working_path(path: str) -> None:
    global _working_path
    _working_path = path


def get_working_path() -> str:
    return _working_path


def set_iteration(n: int) -> None:
    global _current_iteration
    _current_iteration = n


def reset_trace() -> None:
    global _trace, _current_iteration
    _trace = []
    _current_iteration = 1


def record_step(tool: str, args: dict, success: bool, command: list[str], error: str = "") -> None:
    _trace.append({
        "iteration": _current_iteration,
        "tool": tool,
        "args": args,
        "success": success,
        "command": " ".join(command),
        "error": error,
    })


def get_trace() -> list[dict]:
    return list(_trace)
