[Documentation](/docs/documentation.md) >
 [v0.0](/docs/0.0/version.md) >
  [runtime](/docs/0.0/runtime/module.md) >
   [threading](/docs/0.0/runtime/threading/module.md) >
    terminate_event

# terminate_event: [Event](event.md)

The `terminate_event` variable is an event which is set when application is requested to exit (i.e. it recieves a SIGTERM or SIGINT signal.)

### Example:

```python
from runtime.threading import terminate_event

while not terminate_event.wait(0):
    ...
```