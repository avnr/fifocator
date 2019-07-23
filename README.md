# Fifocator

### Named Pipes made easy

Fifocator enables an easy implementation of named pipes IPC, hiding many
of its tricky details. A fifocator-based worker subscribes functions to
single-line text messages that arrive on a named pipe and then runs a main
loop. The messages can be subscribed to as strings that need to be
matched, or as regular expressions. The main loop polls the named pipe at
an interval, and when a message subscribed to arrives it dispatches the
subscribed function. The worker can have a function called at the polling
interval by subscribing that function to an empty message. Subscribing a
function without specifying a message subscribes the function to a
wildcard message, i.e., any message not intercepted by another subscribed
function. If there are several subscribers that match a message then the
first subscribed match is that one that will be called.

Setting up a named pipe:

```
from fifocator import Fifo

my_worker = Fifo('my_fifo_file')
```

In the above example the named pipe will automatically be opened at the
/tmp directory. To open the file at another location please specify its
full path.

Subscribing a function to a message:

```
# subscribe to string "message text"
my_worker.sub(f, 'message text')

# subscribe to any message that matches the regular expression
my_worker.sub(f, re.compile('^.$'))

# convenience function for subscribing to regular expressions
my_worker.sub_re(f, '^.$')

# wildcard subscription
my_worker.sub(f)

# get called on every poll
my_worker.sub(f,'')
```

The function `f` in the above examples will receive two arguments, the message
that emitted the call to the function and the name of the pipe on which
it was received. It can be defined as follows:

```
def f(msg, name):
    pass           # or whatever you want to do when the message arrives
```

Running the main loop:

```
# poll every 100ms
my_worker.run(0.1)
```

To quit the main loop raise the `Quit` exception:

```
from fifocator import Fifo, Quit

def f(msg, name):
    print('Got some message')

def quit_(msg, name):
    raise Quit

if __name__ == '__main__':
    my_worker = Fifo('my_fifo_file')
    my_worker.sub(f)
    my_worker.sub(quit_,'quit')
    my_worker.run(0.1)
```

Sending messages to the named pipe can be easily done from the command line:

```
$ echo message text > /tmp/my_fifo_file
```

You can also use fifocator to implement the client side, first set up the
named pipe:

```
from fifocator import Fifo

my_client = Fifo('my_fifo_file')
```

Write something to the pipe:

```
my_client.put('something')
```

Check out some more examples in the code and in test.py in the test
directory.

### Installation

Fifocator has no external dependencies so you can just drop the file
fifocator.py in place.

You can also install it in the library using setuptools.

REQUIRES PYTHON3.6 OR ABOVE.

### License

MIT License.

