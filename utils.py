#!/usr/bin/env python
# encoding: utf-8
import signal
import os
import sys

#import eventlet.wsgi
#eventlet.patcher.monkey_patch(all=False, thread=None, socket=True)
#from neutron.openstack.common import loopingcall as ll
#moudule_dir = os.path.normpath(os.path.join(os.path.abspath(sys.argv[0]),
#                            os.pardir,os.pardir))
#sys.path.insert(0, moudule_dir)

from eventlet import event
from eventlet.green import subprocess
from eventlet import greenthread

from torconf import timeutils

class LocalVLanBitmap(object):
    """Setup a VLAN bitmap for allocation or de-allocation."""

    def __init__(self, min, max):
        """Initialize the VLAN set."""
        self.min = min
        self.max = max
        self.size = self.get_array(max, True)
        self.array = [0 for i in range(self.size)]

    def __repr__(self):
        return "{\"LocalVLanBitmap\": \"%s\"}" %(self.array)

    def get_array(self, num, up=False):
        if up:
            return (num + 31 - 1) / 31
        return num / 31

    def get_bit_location(self, num):
        return num % 31

    def add_bits(self, num):
        """mask a bit"""
        elemIndex = self.get_array(num)
        byteIndex = self.get_bit_location(num)
        elem = self.array[elemIndex]
        self.array[elemIndex] = elem | (1 << (31 - byteIndex))

    def delete_bits(self, num):
        """Delete a in used bit."""
        elemIndex = self.get_array(num)
        byteIndex = self.get_bit_location(num)
        elem = self.array[elemIndex]
        self.array[elemIndex] = elem & (~(1 << (31 - byteIndex)))

    def get_unused_bits(self):
        """retrieve an unused vlan number"""
        for bits in range(self.min, self.max + 1):
            if self._bit_on(bits):
                continue
            self.add_bits(bits)
            return bits
        return None

    def _bit_on(self, bits):
        elemIndex = self.get_array(bits)
        byteIndex = self.get_bit_location(bits)
        if self.array[elemIndex] & (1 << (31 - byteIndex)):
            return True
        return False

def _subprocess_setup():
    # Python installs a SIGPIPE handler by default. This is usually not what
    # non-Python subprocesses expect.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def subprocess_popen(args, stdin=None, stdout=None, stderr=None, shell=False,
                     env=None):
    return subprocess.Popen(args, shell=shell, stdin=stdin, stdout=stdout,
                            stderr=stderr, preexec_fn=_subprocess_setup,
                            close_fds=True, env=env)

def execute(cmd, check_exit_code=True):
    try:
        cmd = map(str, cmd)
        obj = subprocess_popen(cmd, shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=os.environ.copy())

        _stdout, stderr = obj.communicate()
        obj.stdin.close()

        m = "cmd: %s exit code: %s." %(cmd, obj.returncode)
        if obj.returncode and check_exit_code:
            raise RuntimeError(m)
    finally:
        greenthread.sleep(0)

    return _stdout

class LoopingCallDone(Exception):
    def __init__(self, retvalue=True):
        """:param retvalue: Value that LoopingCall.wait() should return."""
        self.retvalue = retvalue

class LoopingCallBase(object):
    def __init__(self, f=None, *args, **kw):
        self.args = args
        self.kw = kw
        self.f = f
        self._running = False
        self.done = None

    def stop(self):
        self._running = False

    def wait(self):
        return self.done.wait()


class FixedIntervalLoopingCall(LoopingCallBase):
    """A fixed interval looping call."""

    def start(self, interval, initial_delay=None):
        self._running = True
        done = event.Event()

        def _inner():
            if initial_delay:
                greenthread.sleep(initial_delay)

            try:
                while self._running:
                    start = timeutils.utcnow()
                    self.f(*self.args, **self.kw)
                    end = timeutils.utcnow()
                    if not self._running:
                        break
                    delay = interval - timeutils.delta_seconds(start, end)
                    greenthread.sleep(delay if delay > 0 else 0)
            except LoopingCallDone as e:
                self.stop()
                done.send(e.retvalue)
            except Exception:
                done.send_exception(*sys.exc_info())
                return
            else:
                done.send(True)

        self.done = done

        greenthread.spawn_n(_inner)
        return self.done

def FixedIntervalLoopingCallFunc(f):
    def __inner():
        while True:
            f()
    greenthread.spawn_n(__inner)

def regular():
    print "test"

if __name__ == "__main__":
    #cmd =  ['snmpwalk', '-v', '2c', '-c', 'public', '10.216.24.101', '.1.0.8802.1.1.2.1.3']
    #output = execute(cmd)
    #for line in [line for line in output.split('\n') if line != '']:
    #    print line

    loop = FixedIntervalLoopingCall(regular)
    loop.start(interval=1)

    greenthread.sleep(10)

    #loop = FixedIntervalLoopingCall(regular)
    #loop.start(interval=2)
