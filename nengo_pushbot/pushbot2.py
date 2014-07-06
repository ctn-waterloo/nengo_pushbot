import socket
import time
import numpy as np
import struct
import atexit

class PushBot2(object):
    def __init__(self, address, port=56000, message_delay=0.01):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))
        self.socket.settimeout(0)
        self.message_delay = message_delay
        self.last_time = {}

        self.motor(0, 0, force=True)
        self.socket.send('E+\n')
        self.socket.send('!M+\n')
        atexit.register(self.stop)

        self.ticks = 0
        self.vertex = None

    def send(self, key, cmd, force):
        now = time.time()
        if force or self.last_time.get(key, None) is None or (now >
                self.last_time[key]+self.message_delay):
            self.socket.send(cmd)
            #print cmd
            self.last_time[key] = now

    def motor(self, left, right, force=False):
            left = int(left*100)
            right = int(right*100)
            if left > 100: left=100
            if left < -100: left=-100
            if right > 100: right=100
            if right < -100: right=-100
            cmd = '!MVD0=%d\n!MVD1=%d\n' % (left, right)
            self.send('motor', cmd, force)
    def beep(self, freq, force=False):
        if freq <= 0:
            cmd = '!PB=0\n!PB0=0\n'
        else:
            cmd = '!PB=%d\n!PB0=%%50\n' % int(1000000/freq)
        self.send('beep', cmd, force)
    def laser(self, freq, force=False):
        if freq <= 0:
            cmd = '!PA=0\n!PA0=0\n'
        else:
            cmd = '!PA=%d\n!PA0=%d\n' % (int(1000000/freq), int(500000/freq))
        self.send('laser', cmd, force)
    def led(self, freq, force=False):
        if freq <= 0:
            cmd = '!PC=0\n!PC0=0\n!PC1=0'
        else:
            cmd = '!PC=%d\n!PC0=%%50\n!PC1=%%50' % int(1000000/freq)
        self.send('led', cmd, force)

    def stop(self):
        if self.socket is not None:
            self.beep(0, force=True)
            #self.laser(0, force=True)
            #self.led(0, force=True)
            self.socket.send('!M-\n')
            self.socket.send('E-\n')
            #self.send_motor(0, 0, force=True)

