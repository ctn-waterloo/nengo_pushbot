import nengo
import nengo_pushbot

class PushBotNetwork(nengo.Network):
    def __init__(self, addr, port=56000):
        self.bot = nengo_pushbot.PushBot3.get_bot(addr, port)
        self.label = 'PushBot'
        self._motor = None
        self._beep = None
        self._compass = None
        self._gyro = None
        self._accel = None
        self._touch = None

    def laser(self, freq):
        self.bot.laser(freq, force=True)

    def led(self, freq):
        self.bot.led(freq, force=True)

    def count_spikes(self, **regions):
        self.bot.count_spikes(**regions)
        with self:
            for k in regions.keys():
                node = nengo_pushbot.CountSpikes(self.bot, k)
                setattr(self, 'count_%s' % k, node)

    def track_freqs(self, freqs):
        self.bot.track_freqs(freqs)
        with self:
            for i in range(len(freqs)):
                node = nengo_pushbot.Tracker(self.bot, i)
                setattr(self, 'tracker_%d' % i, node)

    def show_image(self, decay=0.5):
        self.bot.show_image(decay=decay)

    @property
    def touch(self):
        if self._touch is None:
            with self:
                self._touch = nengo_pushbot.Touch(self.bot)
        return self._touch

    @property
    def motor(self):
        if self._motor is None:
            with self:
                self._motor = nengo_pushbot.Motor(self.bot)
        return self._motor

    @property
    def beep(self):
        if self._beep is None:
            with self:
                self._beep = nengo_pushbot.Beep(self.bot)
        return self._beep


    @property
    def compass(self):
        if self._compass is None:
            self.bot.activate_sensor('compass', freq=100)
            with self:
                self._compass = nengo_pushbot.Compass(self.bot)
        return self._compass

    @property
    def gyro(self):
        if self._gyro is None:
            self.bot.activate_sensor('gyro', freq=100)
            with self:
                self._gyro = nengo_pushbot.Gyro(self.bot)
        return self._gyro

    @property
    def accel(self):
        if self._accel is None:
            self.bot.activate_sensor('accel', freq=100)
            with self:
                self._accel = nengo_pushbot.Accel(self.bot)
        return self._accel
