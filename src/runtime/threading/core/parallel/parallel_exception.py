from runtime.threading.core.threading_exception import ThreadingException

class ParallelException(ThreadingException):
    """The ParallelException exception is raised within the runtime.threading.parallel module whenever
    a precondition fails.
    """
    pass