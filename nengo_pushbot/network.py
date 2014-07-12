import nengo
import nengo_pushbot

class PushBotNetwork(nengo.Network):
    def __init__(self, addr, port=56000, message_delay=0.01, packet_size=5):
        self.bot = nengo_pushbot.PushBot3.get_bot(addr, port,
                                                  message_delay=message_delay,
                                                  packet_size=packet_size)
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
            for (k, r) in regions.items():
                node = nengo_pushbot.CountSpikes(self.bot, k, r)
                setattr(self, 'count_%s' % k, node)

    def track_freqs(self, freqs, sigma_t=100, sigma_p=30, eta=0.3):
        self.bot.track_freqs(freqs, sigma_t=sigma_t, sigma_p=sigma_p, eta=eta)
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
