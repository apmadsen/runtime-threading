from multiprocessing import cpu_count

DEFAULT_PARALLELISM = cpu_count()
TASK_SUSPEND_AFTER = 0.1 # any less than 0.1 may cause stack owerflow
TASK_KEEP_ALIVE = 0.1
POLL_INTERVAL = 0.1