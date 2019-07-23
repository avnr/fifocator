#!/usr/bin/python3

#
# How to run the tests:
#
# 1. Basic Testing
# ----------------
#
# Run the worker:
# $ python3.7 test.py worker
#
# In a seperate terminal run a client:
# $ python3.7 test.py
#
# You can also send some arbitrary messages to the worker:
# $ echo lorem ipsum > /tmp/fifocator.fifo
#
# When the client finishes sending messages it will quit, and you can
# also quit the worker:
# $ echo quit > /tmp/fifocator.fifo
#
# The worker can be also gracefully terminated by CRTL-C.
#
# 2. Badass Testing
# -----------------
#
# Run the worker in the background and save its output in a log file:
# $ python3.7 test.py worker > w1.log &
#
# Run multiple clients in background, save their outputs in log files:
# $ python3.7 test.py > c1.log &
# $ python3.7 test.py > c2.log &
# $ python3.7 test.py > c3.log &
# ...
#
# When the clients finish running, quit the worker:
# $ echo quit > /tmp/fifocator.fifo
#
# Compare the logs files to verify that no message went missing or 
# duplicate:
# $ cat c?.log | sort > c.log
# $ sort w1.log > w.log
# $ diff w.log c.log
#
# NOTES:
# ------
#
# If you want to run more clients than your number of cores less 1 then
# you may need to reduce the cpu loads per message and the ratio 
# between client & worker intervals using the constants below.
#

import random
import sys

from time import sleep

sys.path.insert(0, '..')
import fifocator


FIFO_NAME = 'fifocator.fifo'

XMISSIONS_PER_CLIENT = 1000         # To get the kick start small, eg 10
MESSAGES_PER_XMISSION = 2
INTERVAL_BETWEEN_XMISSIONS = 1
CLIENT_LOAD_PER_MESSAGE = 2**16     # ~5% CPU load on a 8250U
WORKER_LOAD_PER_MESSAGE = 2**16     #
WORKER_INTERVAL = 0.1

DICTIONARY = ('X-----', '-X----', '--X---', '---X--', '---X-', '-----X' )

def distort(n, p=0.35):
    """
    Distort values with sigma as percent of value
    """
    return int(random.gauss(n, n*p))


def mk_load(n):
    """
    Generates cpu-bound load
    """
    n = distort(n,0.1)
    k = 1.1
    while n:
        n -= 1
        k *= 1.1
        if k > sys.maxsize/2:
            k = 1.1
    return k


def client():
    global fifo
    n = distort(XMISSIONS_PER_CLIENT)
    while n:
        n -= 1
        k = distort(MESSAGES_PER_XMISSION)
        msgs = random.choices(DICTIONARY,k=k)
        while k:
            k -=1
            fifo.put(msgs[k])
            print(msgs[k])
            mk_load(CLIENT_LOAD_PER_MESSAGE)
        sleep(INTERVAL_BETWEEN_XMISSIONS)


def worker():
    global fifo

    def _worker(msg, name):
        if msg != '':
            print(msg)
            mk_load(WORKER_LOAD_PER_MESSAGE)

    def _quit(msg, name):
        exit()

    def _wildcard(msg, name):
        print(f'Unknown message: {msg}')

    def _never_called(msg, name):
        print('Holly bologna o_O')

    fifo.sub(_wildcard)
    fifo.sub(_worker, '')
    fifo.sub(_worker, 'X-----')
    fifo.sub(_worker, '-X----')
    fifo.sub_re(_worker, '^--.*X.*-$')
    fifo.sub(_never_called, '---X--')
    fifo.sub(_worker, '-----X')
    fifo.sub(_quit, 'quit')

    try:
        fifo.run(WORKER_INTERVAL)
    except KeyboardInterrupt:
        print('Stopped by CTRL-C')
        exit()


if __name__ == '__main__':
    random.seed()
    fifo = fifocator.Fifo(FIFO_NAME)
    if len(sys.argv) == 2 and sys.argv[1] == 'worker':
        worker()
    elif len(sys.argv) == 1:
        client()
    else:
        print('test.py [worker]')

