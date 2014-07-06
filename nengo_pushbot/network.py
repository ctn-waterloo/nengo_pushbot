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
