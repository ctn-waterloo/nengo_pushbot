import nengo

class Gyro(nengo.Node):
    def __init__(self, bot, label='gyro'):
        self.bot = bot
        super(Gyro, self).__init__(self.gyro_input, size_out=3,
                                     label=label)

    def gyro_input(self, t):
        if self.bot is not None:
            return self.bot.get_gyro()
        else:
            return [0, 0, 0]
