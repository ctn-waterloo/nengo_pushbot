import nengo

class Accel(nengo.Node):
    def __init__(self, bot, label='accel'):
        self.bot = bot
        super(Accel, self).__init__(self.accel_input, size_out=3,
                                     label=label)

    def accel_input(self, t):
        if self.bot is not None:
            return self.bot.get_accel()
        else:
            return [0, 0, 0]
