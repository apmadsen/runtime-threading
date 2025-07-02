from multiprocessing import cpu_count

DEFAULT_PARALLELISM = min(4, max(2, cpu_count())) # due to the fact that Python isn't truly multithreaded, a max of 4 shouldn't be exceeded for the default value
TASK_SUSPEND_AFTER = 0.1 # any less than 0.1 may cause stack owerflow
TASK_KEEP_ALIVE = 0.1
POLL_INTERVAL = 0.1