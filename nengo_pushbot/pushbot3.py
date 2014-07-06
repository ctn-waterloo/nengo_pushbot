import socket
import time
import numpy as np
import struct
import atexit
import thread




class PushBot3(object):
    sensors = dict(compass=512, accel=256, gyro=128)

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
        self.key = (address, port)
        self.message_delay = message_delay
        self.last_time = {}

        self.motor(0, 0, force=True)
        self.socket.send('\n\nR\n\n')  # reset the board
        time.sleep(2)
        self.socket.send('!E2\nE+\n')  # turn on retina
        self.socket.send('!M+\n')      # activate motors
        atexit.register(self.stop)
        print '...connected'

        self.ticks = 0
        self.vertex = None

        self.sensor = dict(compass=[0,0,0], accel=[0,0,0], gyro=[0,0,0])
        self.compass_range = None

        self.image = None
        thread.start_new_thread(self.sensor_loop, ())

    def show_image(self):
        if self.image is None:
            self.image = np.zeros((128, 128), dtype=float)
            thread.start_new_thread(self.image_loop, ())



    def image_loop(self):
        import pylab
        pylab.ion()
        img = pylab.imshow(self.image, vmax=1, vmin=-1,
                                       interpolation='none', cmap='binary')
        while True:
            pylab.draw()
            pylab.pause(0.00001)
            img.set_data(self.image)
            self.image *= 0.5

    def get_compass(self):
        return self.sensor['compass']
    def get_accel(self):
        return self.sensor['accel']
    def get_gyro(self):
        return self.sensor['gyro']

    def set_accel(self, data):
        x, y, z = data
        self.sensor['accel'] = float(x)/10000, float(y)/10000, float(z)/10000

    def set_gyro(self, data):
        x, y, z = data
        self.sensor['gyro'] = float(x)/5000, float(y)/5000, float(z)/5000

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
        index = msg.find('-')
        if index > -1:
            msg = msg[index:]
            try:
                if msg.startswith('-S9 '):
                    x,y,z = msg[4:].split(' ')
                    self.set_compass((int(x), int(y), int(z)))
                elif msg.startswith('-S8 '):
                    x,y,z = msg[4:].split(' ')
                    self.set_accel((int(x), int(y), int(z)))
                elif msg.startswith('-S7 '):
                    x,y,z = msg[4:].split(' ')
                    self.set_gyro((int(x), int(y), int(z)))
                else:
                    pass
                    #print 'unknown msg', msg
            except:
                pass
                #print 'invalid msg', msg

    def sensor_loop(self):
        old_data = None
        buffered_ascii = ''
        while True:
            try:
                data = self.socket.recv(1024)
                if old_data is not None:
                    data = old_data + data
                data_all = np.fromstring(data, np.uint8)
                ascii_index = np.where(data_all[::4] < 0x80)[0]

                offset = 0
                while len(ascii_index) > 0:
                    index = ascii_index[0]*4
                    stop_index = np.where(data_all[index:] >=0x80)[0]
                    if len(stop_index) > 0:
                        stop_index = index + stop_index[0]
                    else:
                        stop_index = len(data)
                    buffered_ascii += data[offset+index:offset+stop_index]
                    data_all = np.hstack((data_all[:index], data_all[stop_index:]))
                    offset += stop_index - index
                    ascii_index = np.where(data_all[::4] < 0x80)[0]

                extra = len(data_all) % 4
                if extra != 0:
                    old_data = data[-extra:]
                    data_all = data_all[:-extra]
                self.process_retina(data_all)

                while '\n' in buffered_ascii:
                    cmd, buffered_ascii = buffered_ascii.split('\n', 1)
                    self.process_ascii(cmd)

            except socket.error as e:
                pass

    def process_retina(self, data):
        if self.image is not None:
            x = data[::4] & 0x7f
            y = data[1::4] & 0x7f
            value = np.where(data[1::4]>=0x80, 1, -1)
            self.image[x, y] += value
        assert len(data) % 4 == 0

    def send(self, key, cmd, force):
        now = time.time()
        if force or self.last_time.get(key, None) is None or (now >
                self.last_time[key] + self.message_delay):
            self.socket.send(cmd)
            self.last_time[key] = now

    def activate_sensor(self, name, freq):
        bitmask = PushBot3.sensors[name]
        period = int(1000.0/freq)
        try:
            self.socket.send('!S+%d,%d\n' % (bitmask, period))
        except:
            self.diconnect()

    def disconnect(self):
        del PushBot3.running_bots[self.key]
        self.socket.close()


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
    bot = PushBot3('10.162.177.55')
    bot.activate_sensor('compass', freq=100)
    bot.activate_sensor('gyro', freq=100)
    bot.show_image()
    import time

    while True:
        time.sleep(1)

