from enum import IntFlag

class ContinuationOptions(IntFlag):
    INLINE = 1
    ON_COMPLETED_SUCCESSFULLY = 2
    ON_FAILED = 8
    ON_CANCELED = 16
    DEFAULT = 27