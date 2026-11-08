class MLComponentNotImplemented(RuntimeError):
    """Raised by every placeholder ML interface implementation in this
    package. Never caught-and-silently-replaced-with-a-fake-result
    anywhere in this codebase -- callers must either implement a real
    component or let this propagate, by design."""
