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
    def get_bot(cls, address, port=56000):
        key = (address, port)
        if key not in PushBot3.running_bots:
            PushBot3.running_bots[key] = PushBot3(address, port)
        return PushBot3.running_bots[key]


    def __init__(self, address, port=56000, message_delay=0.01):
        self.image = None
        self.regions = None
        self.track_periods = None
        self.spinnaker_address = None

        self.laser_freq = None
        self.led_freq = None

        if ',' in address:
            print 'configuring for SpiNNaker', address
            self.spinnaker_address = address.split(',')
            self.socket = None
            return
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

        thread.start_new_thread(self.sensor_loop, ())

    def count_spikes(self, **regions):
        self.regions = regions
        self.count_regions = {}
        for k,v in regions.items():
            self.count_regions[k] = [0, 0]
    def track_freqs(self, freqs):
        freqs = np.array(freqs, dtype=float)
        self.track_periods = 500000/freqs

        self.last_on = np.zeros((128, 128), dtype=np.uint16)
        self.last_off = np.zeros((128, 128), dtype=np.uint16)
        self.p_x = np.zeros_like(self.track_periods) + 64.0
        self.p_y = np.zeros_like(self.track_periods) + 64.0
        self.good_events = np.zeros_like(self.track_periods, dtype=int)



    def get_spike_rate(self, region):
        return self.count_regions[region][0]


    def show_image(self, decay = 0.5):
        if self.socket is None:
            # TODO: log a warning here
            return
        if self.image is None:
            self.image = np.zeros((128, 128), dtype=float)
            thread.start_new_thread(self.image_loop, (decay,))


    def image_loop(self, decay):
        import pylab
        fig = pylab.figure()
        pylab.ion()
        img = pylab.imshow(self.image, vmax=1, vmin=-1,
                                       interpolation='none', cmap='binary')

        while True:
            img.set_data(self.image)
            pylab.pause(0.001)
            #fig.canvas.draw()
            #fig.canvas.flush_events()
            self.image *= decay

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
        if data[0] == 0 and data[1] == 0 and data[2] == 0:
            # throw out invalid data
            return
        if self.compass_range is None:
            self.compass_range = np.array([data, data], dtype=float)
        else:
            for i in range(3):
                self.compass_range[0][i] = max(data[i],
                                               self.compass_range[0][i])
                self.compass_range[1][i] = min(data[i],
                                               self.compass_range[1][i])

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
                    data_all = np.hstack((data_all[:index],
                                          data_all[stop_index:]))
                    offset += stop_index - index
                    ascii_index = np.where(data_all[::4] < 0x80)[0]

                extra = len(data_all) % 4
                if extra != 0:
                    old_data = data[-extra:]
                    data_all = data_all[:-extra]
                if len(data_all) > 0:
                    self.process_retina(data_all)

                while '\n' in buffered_ascii:
                    cmd, buffered_ascii = buffered_ascii.split('\n', 1)
                    self.process_ascii(cmd)

            except socket.error as e:
                pass

    def process_retina(self, data):
        x = data[::4] & 0x7f
        y = data[1::4] & 0x7f
        if self.image is not None:
            value = np.where(data[1::4]>=0x80, 1, -1)
            self.image[x, y] += value
        if self.regions is not None:
            tau = 0.05 * 1000000
            for k, region in self.regions.items():
                minx, miny, maxx, maxy = region
                index = (minx <= x) & (x<maxx) & (miny <= y) & (y<maxy)
                count = np.sum(index)
                time = (int(data[-2]) << 8) + data[-1]

                old_count, old_time = self.count_regions[k]

                dt = time - old_time
                if dt < 0:
                    dt += 65536

                decay = np.exp(-dt/tau)
                new_count = old_count * decay + count * (1-decay)

                self.count_regions[k] = new_count, time
            #print {k:v[0] for k,v in self.count_regions.items()}

        if self.track_periods is not None:
            time = data[2::4].astype(np.uint16)
            time = (time << 8) + data[3::4]
            index_on = (data[1::4] & 0x80) > 0
            index_off = (data[1::4] & 0x80) == 0

            delta = np.where(index_on,
                             time - self.last_off[x, y],
                             time - self.last_on[x, y])

            self.last_on[x[index_on],
                         y[index_on]] = time[index_on]
            self.last_off[x[index_off],
                          y[index_off]] = time[index_off]

            for i, period in enumerate(self.track_periods):
                eta = 0.2
                t_exp = period
                sigma_t = 100
                t_diff = delta.astype(np.float) - t_exp

                w_t = np.exp(-(t_diff**2)/(2*sigma_t**2))
                # haven't done w_p yet

                # horrible heuristic for figuring out if we have good
                # data by chekcing the proportion of events that are
                # within sigma_t of desired period
                self.good_events[i] += (w_t>0.5).sum()

                # update position estimate
                try:
                    r_x = np.average(x, weights=w_t)
                    r_y = np.average(y, weights=w_t)
                    self.p_x[i] = (1-eta)*self.p_x[i] + (eta)*r_x
                    self.p_y[i] = (1-eta)*self.p_y[i] + (eta)*r_y
                except ZeroDivisionError:
                    # occurs in np.average if weights sum to zero
                    pass
            print self.p_x, self.p_y

    def send(self, key, cmd, force):
        if self.socket is None:
            return
        now = time.time()
        if force or self.last_time.get(key, None) is None or (now >
                self.last_time[key] + self.message_delay):
            self.socket.send(cmd)
            self.last_time[key] = now

    def activate_sensor(self, name, freq):
        if self.socket is None:       # spinnaker
            return
        bitmask = PushBot3.sensors[name]
        period = int(1000.0/freq)
        try:
            self.socket.send('!S+%d,%d\n' % (bitmask, period))
        except:
            self.disconnect()

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
        if self.socket is not None:
            if freq <= 0:
                cmd = '!PA=0\n!PA0=0\n'
            else:
                cmd = '!PA=%d\n!PA0=%d\n' % (int(1000000/freq),
                                             int(500000/freq))
            self.send('laser', cmd, force)
        else:
            self.laser_freq = freq

    def led(self, freq, force=False):
        if self.socket is not None:
            if freq <= 0:
                cmd = '!PC=0\n!PC0=0\n!PC1=0'
            else:
                cmd = '!PC=%d\n!PC0=%%50\n!PC1=%%50' % int(1000000/freq)
            self.send('led', cmd, force)
        else:
            self.led_freq = freq

    def stop(self):
        if self.socket is not None:
            self.beep(0, force=True)
            #self.laser(0, force=True)
            #self.led(0, force=True)
            self.socket.send('!M-\n')
            self.socket.send('E-\n')
            self.socket.send('!S-\n')


if __name__ == '__main__':
    #bot = PushBot3('10.162.177.44')
    bot = PushBot3('1,0,EAST')
    bot.activate_sensor('compass', freq=100)
    bot.activate_sensor('gyro', freq=100)
    bot.count_spikes(all=(0,0,128,128), left=(0,0,128,64), right=(0,64,128,128))
    bot.laser(100)
    bot.track_freqs([100])
    bot.show_image()
    import time

    while True:
        time.sleep(1)

