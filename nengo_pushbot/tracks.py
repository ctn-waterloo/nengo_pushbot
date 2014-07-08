import nengo


class Tracks(nengo.Node):

    def __init__(self, bot, label='tracks'):
        self.bot = bot
        super(Tracks, self).__init__(output=self.motor_output, size_in=2,
                                     label=label)

    def motor_output(self, t, x):
        if self.bot is not None:
            self.bot.send_motor(x[0], x[1])
        return []
