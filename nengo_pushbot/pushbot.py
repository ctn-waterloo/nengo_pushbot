import socket
import time
import numpy as np
import struct
import atexit

class PushBot(object):
    def __init__(self, address, port=56000, message_delay=0.01):
        if isinstance(address, str):
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((address, port))
            self.last_message_time = None
            self.socket.settimeout(0)
            self.message_delay = message_delay

            self.send_motor(0, 0, force=True)
            self.socket.send('E+\n')
            atexit.register(self.stop)

        else:
            self.socket = None

        self.view = np.zeros((128, 128), dtype=float)
        self.ticks = 0


    def send_motor(self, left, right, force=False):
        assert self.socket is not None
        now = time.time()
        if force or self.last_message_time is None or (now >
                (self.last_message_time + self.message_delay)):
            left = int(left*100)
            right = int(right*100)
            if left > 100: left=100
            if left < -100: left=-100
            if right > 100: right=100
            if right < -100: right=-100
            cmd = '!M0=%d\n!M1=%d\n' % (left, right)
            #print cmd

            self.socket.send(cmd)
            self.last_message_time = now
        return []
    def stop(self):
        if self.socket is not None:
            self.socket.send('E-\n')
            self.send_motor(0, 0, force=True)


    def update_sensors(self, t):
        assert self.socket is not None
        self.ticks += 1
        self.view *= 0
        try:
            old_data = None
            while True:
                data = self.socket.recv(256)
                if old_data is not None:
                    data = old_data + data
                if len(data) % 2 == 1:
                    old_data = data[-1:]
                    data = data[:-1]
                data_all = np.fromstring(data, dtype=np.uint8)
                data_x = data_all[::2]

                errors = np.where(data_x >= 0x80)[0]
                if len(errors) > 0:
                    old_data = data[errors[0]*2+1:]
                    continue

                data_x = data_x & 0x7F
                sign = np.where(data_all[1::2] & 0x80 > 0, 1, -1)
                data_y = data_all[1::2] & 0x7F
                self.view[data_x, data_y] += sign

                self.data_x = data_x
                self.data_y = data_y
                self.sign = sign

        except socket.error:
            pass
        return []







