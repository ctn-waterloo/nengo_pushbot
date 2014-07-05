import socket
import time
import numpy as np
import struct
import atexit
import thread




class PushBot3(object):
    sensors = dict(compass=512)

    running_bots = {}

    @classmethod
    def get_bot(klass, address, port=56000):
        key = (address, port)
        if key not in PushBot3.running_bots:
            PushBot3.running_bots[key] = PushBot3(address, port)
        return PushBot3.running_bots[key]


    def __init__(self, address, port=56000, message_delay=0.01):
        print 'connecting...', address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((address, port))
        self.socket.settimeout(0)
        self.message_delay = message_delay
        self.last_time = {}

        self.motor(0, 0, force=True)
        self.socket.send('\n\nR\n\n')  # reset the board
        time.sleep(5)
        #self.socket.send('E+\n')       # turn on retina
        self.socket.send('!M+\n')      # activate motors
        atexit.register(self.stop)

        self.ticks = 0
        self.vertex = None

        self.sensor = dict(compass=[0,0,0])
        self.compass_range = None
        thread.start_new_thread(self.sensor_loop, ())

    def get_compass(self):
        return self.sensor['compass']

    def set_compass(self, data):
        if self.compass_range is None:
            self.compass_range = np.array([data, data], dtype=float)
        else:
            for i in range(3):
                self.compass_range[0][i] = max(data[i], self.compass_range[0][i])
                self.compass_range[1][i] = min(data[i], self.compass_range[1][i])

        diff = self.compass_range[0] - self.compass_range[1]
        value = [0, 0, 0]
        for i in range(3):
            if diff[i] > 0:
                value[i] = ((data[i]-self.compass_range[1][i])/diff[i] - 0.5) *2
        self.sensor['compass'] = value







    def process_ascii(self, msg):
        #try:
            if msg.startswith('-S9 '):
                x,y,z = msg[4:].split(' ')
                self.set_compass((int(x), int(y), int(z)))
            else:
                print 'unknown msg', msg
        #except:
        #    print 'invalid msg', msg

    def sensor_loop(self):
        old_data = None

        self.buffered_ascii = ''
        while True:
            try:
                data = self.socket.recv(1024)
                #if old_data is not None:
                #    data = old_data + data
                #    old_data = None

                while '\n' in data:
                    cmd, data = data.split('\n', 1)
                    self.process_ascii(self.buffered_ascii + cmd)
                    self.buffered_ascii = ''

                self.buffered_ascii += data


                """
                data_all = np.fromstring(data, np.unit8)
                ascii_all = np.where(data_all < 0x80)[0]
                data_x = data_all[::4]
                ascii_x = asci_all[::4]
                if len(ascii_x) > 0:
                    index = ascii_x[0]*4
                    ascii = asci_all[index:]
                    nonascii =
                """
            except socket.error:
                pass






    def send(self, key, cmd, force):
        now = time.time()
        if force or self.last_time.get(key, None) is None or (now >
                self.last_time[key]+self.message_delay):
            self.socket.send(cmd)
            self.last_time[key] = now

    def activate_sensor(self, name, freq):
        bitmask = PushBot3.sensors[name]
        period = int(1000.0/freq)
        self.socket.send('!S+%d,%d\n' % (bitmask, period))


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
            self.socket.send('!S-\n')


if __name__ == '__main__':
    bot = PushBot3('10.162.177.51')
    time.sleep(2)
    bot.activate_sensor('compass', freq=10)
    import time

    while True:
        time.sleep(1)

