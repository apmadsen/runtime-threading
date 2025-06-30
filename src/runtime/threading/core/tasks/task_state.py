from enum import IntEnum

class TaskState(IntEnum):
    NOTSTARTED = 0
    SCHEDULED = 1
    RUNNING = 2
    COMPLETED = 3
    INTERRUPTED = 4
    FAILED = 5