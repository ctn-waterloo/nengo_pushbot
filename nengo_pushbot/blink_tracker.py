import socket
import time
import thread
import numpy as np

class BlinkTracker(object):
    def __init__(self, socket, freqs):
        self.socket = socket
        self.socket.settimeout(0)
        time.sleep(0.5)
        self.socket.send('\n\n!E2\nE+\n')
        freqs = np.array(freqs, dtype=float)
        self.periods = 500000/freqs

        self.image = np.zeros((128, 128), dtype=float)
        self.last_on = np.zeros((128, 128), dtype=np.uint16)
        self.last_off = np.zeros((128, 128), dtype=np.uint16)
        self.p_x = np.zeros_like(self.periods) + 64.0
        self.p_y = np.zeros_like(self.periods) + 64.0
        self.event_count = 0
        self.good_events = np.zeros_like(self.periods, dtype=int)
        thread.start_new_thread(self.update_loop, ())

    def clear_image(self):
        self.image *= 0.5

    def certainty(self):
        if self.event_count == 0:
            return np.zeros_like(self.periods)
        c = self.good_events / float(self.event_count)
        self.good_events *= 0
        self.event_count = 0
        return c

    def update_loop(self):
        old_data = None
        while True:
            try:
                # read a block of events at a time
                data = self.socket.recv(1024)
                if old_data is not None:
                    data = old_data + data
                    old_data = None

                # conver to bytes
                data_all = np.fromstring(data, np.uint8)

                # detect transmission errors
                data_x = data_all[::4]
                errors = np.where(data_x < 0x80)[0]
                if len(errors) > 0:
                    print 'error', len(errors)
                    off1 = np.where(data_all[1::4] < 0x80)
                    if len(off1[0]) == 0:
                        data_all = data_all[1:]
                    off2 = np.where(data_all[2::4] < 0x80)
                    if len(off2[0]) == 0:
                        data_all = data_all[2:]
                    off3 = np.where(data_all[3::4] < 0x80)
                    if len(off3[0]) == 0:
                        data_all = data_all[3:]
                    data_x = data_all[::4]

                if len(data_all) % 4 != 0:
                    old_data = data[-(len(data_all)%4):]
                    data_all = data_all[:-(len(data_all)%4)]
                    data_x = data_all[::4]

                # start algorithm
                data_x = data_x & 0x7F
                data_y = data_all[1::4]
                index_on = (data_y & 0x80) > 0
                index_off = (data_y & 0x80) == 0
                sign = np.where(index_on, 1, -1)
                data_y &= 0x7F
                self.image[data_x, data_y] += sign

                time = data_all[2::4].astype(np.uint16)
                time = (time << 8) + data_all[3::4]

                delta = np.where(index_on,
                                 time - self.last_off[data_x, data_y],
                                 time - self.last_on[data_x, data_y])

                self.last_on[data_x[index_on], data_y[index_on]] = time[index_on]
                self.last_off[data_x[index_off], data_y[index_off]] = time[index_off]

                self.event_count += len(delta)

                # loop through the different frequencies we're looking for
                for i, period in enumerate(self.periods):
                    eta = 0.2
                    t_exp = period
                    sigma_t = 100
                    t_diff = delta.astype(np.float) - t_exp
                    try:
                        w_t = np.exp(-(t_diff**2)/(2*sigma_t**2))
                        # haven't done w_p yet

                        # horrible heuristic for figuring out if we have good
                        # data by chekcing the proportion of events that are
                        # within sigma_t of desired period
                        self.good_events[i] += (w_t>0.5).sum()

                        # update position estimate
                        r_x = np.average(data_x, weights=w_t)
                        r_y = np.average(data_y, weights=w_t)
                        self.p_x[i] = (1-eta)*self.p_x[i] + (eta)*r_x
                        self.p_y[i] = (1-eta)*self.p_y[i] + (eta)*r_y
                    except ZeroDivisionError:
                        pass

            except socket.error:
                pass

if __name__ == '__main__':
    retina = Retina()
    view = RetinaView(retina)
    while True:
        time.sleep(1)
