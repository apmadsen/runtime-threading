from runtime.threading.core.threading_exception import ThreadingException

class TaskException(ThreadingException):
    """The TaskException exception is raised within the runtime.threading.tasks module whenever
    a precondition fails or an error occurs."""
    pass