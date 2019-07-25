#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#    fifocator - Named Pipes Made Easy
#    Copyright (c) 2018 - 2019 Avner Herskovits
#
#    MIT License
#
#    Permission  is  hereby granted, free of charge, to any person  obtaining  a
#    copy of this  software and associated documentation files (the "Software"),
#    to deal in the Software  without  restriction, including without limitation
#    the rights to use, copy, modify, merge,  publish,  distribute,  sublicense,
#    and/or  sell  copies of  the  Software,  and to permit persons to whom  the
#    Software is furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this  permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT  WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE  WARRANTIES  OF  MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR  ANY  CLAIM,  DAMAGES  OR  OTHER
#    LIABILITY, WHETHER IN AN  ACTION  OF  CONTRACT,  TORT OR OTHERWISE, ARISING
#    FROM,  OUT  OF  OR  IN  CONNECTION WITH THE SOFTWARE OR THE  USE  OR  OTHER
#    DEALINGS IN THE SOFTWARE.
#
import os
import re

from errno import EAGAIN, ENOENT, ENXIO, EWOULDBLOCK
from os.path import exists, join
from stat import S_ISFIFO
from time import monotonic, sleep

RE_TYPE = type(re.compile(''))  # for python3.6/3.7 compatibility
FIFO_ROOT = '/tmp'


class FifoDoesNotExistError(Exception):
    """
    This exception is raised when the destination named pipe for writing
    a message does not exist, and after attempting to wait for a worker for
    the number of requested retries.
    """
    def __init__(self,name):
        self.message = f'The named pipe {name} does not exist.'


class NotFifoError(Exception):
    """
    This exception is raised if the path of a requested named pipe points
    to an existing file that is not a named pipe.
    """
    def __init__(self, name):
        self.message=f'{name} is not a named pipe.'


class Quit(Exception): pass


class FifoWorker:
    """
    Invoke a worker that waits for messages sent over named pipes. Messages are
    single-line utf-8 strings, e.g.:

    $ echo my command > /tmp/myfifo.fifo

    Or use the FifoClient class below to create a client.
    """

    def __init__(self, name):
        self.original = name
        self.subscribers = []
        self.wildcard = None
        if name[0] != os.sep:
            name = join(FIFO_ROOT, name)
        self.name = name


    def sub(self, callback, msg=None):
        """
        Subscribe a callable to a message, where the message is a string
        or a regular expression to be matched.

        Omitting the message argument will create a wildcard subscription.

        The callable must accept two strings, the first is the received
        message and the second is the name of the pipe from which it was
        received.

        Only the first subscription that matches a message will be invoked.
 
        OPTIMIZATION HINT: First subscribe to empty messages as they are
        the most common:

        myfifo.sub(f0, '')
        myfifo.sub(f1, 'msg1')
        myfifo.sub(f2, 'msg2')
        ...
        """
        if msg != None:
            self.subscribers += ((type(msg) != RE_TYPE, msg, callback),)
        elif self.wildcard == None:
            self.wildcard = callback


    def sub_re(self, callback, msg):
        """
        Convenience method for subscribing to a regular expression.
        """
        self.sub(callback, re.compile(msg))


    def emit(self, msg):
        """
        Emit call to the callback subscribed to msg.
        """
        for sub in self.subscribers:
            if sub[0] and sub[1] == msg or not sub[0] and re.match(sub[1], msg):
                sub[2](msg, self.original)
                break
        else:
            if self.wildcard:
                self.wildcard(msg, self.original)


    def run(self, interval):
        """
        Main loop, listen to named pipe and emit calls on each message.
        Before starting, first ensures that the named pipe exists.

        Exit the main loop by raising the exception Quit.
        """
        if not exists(self.name):
            umask=os.umask(0o000)
            os.mkfifo(self.name,mode=0o666)
            os.umask(umask)
        elif not S_ISFIFO(os.stat(self.name).st_mode):
            raise NotFifoError(self.name)

        fifo = os.open(self.name, os.O_RDONLY|os.O_NONBLOCK)
        try:
            while True:
                try:
                    _msg = os.read(fifo,9999).decode('utf-8').strip()
                except OSError as err:
                    if err.errno == EAGAIN or err.errno == EWOULDBLOCK:
                        _msg = ''
                    else:
                        raise
                for msg in _msg.split('\n'):
                    self.emit(msg.strip())
                sleep(interval)
        except Quit:
            pass
        os.close(fifo)


    def quit(self, *args, **kwargs):
        """
        Convenience function for raising the Quit exception.
        """
        raise Quit


class FifoClient:

    def __init__(self, name, retries = 3, retry_interval = 0.1, guarantee_delivery = False):
        """
        name - the name of the named pipe, if not provided with an absolute
            path then it is assumed to be under /tmp

        retries - number of retries before failing a write operation

        retry_interval - how long to wait in seconds between retry intervals

        gurantee_delivery - if True and writing to the pipe fails after
            retries then raise an exception; otherwise drop the message,
            and don't retry in subsequent writes until another write suceeds
        """
        self.original = name
        if name[0] != os.sep:
            name = join(FIFO_ROOT, name)
        self.name = name
        self.retries = retries
        self.retries_save = retries
        self.retry_interval = retry_interval
        self.guarantee_delivery = guarantee_delivery


    def write(self, msg):
        """
        Writes a message to a named pipe.
        """
        fifo = None
        while True:
            try:
                fifo = os.open(self.name, os.O_WRONLY|os.O_NONBLOCK)
            except OSError as err:
                if err.errno != ENXIO and err.errno != ENOENT:
                    raise
                else:
                    if self.retries:
                        self.retries -= 1
                        sleep(self.retry_interval)
                    elif self.guarantee_delivery:
                        raise PipeDoesNotExistError(self.name)
                    else:   # drop message
                        break
            else:
                self.retries = self.retries_save
                os.write(fifo, (msg+'\n').encode('utf-8'))
                break
            finally:
                if fifo:
                    os.close(fifo)

