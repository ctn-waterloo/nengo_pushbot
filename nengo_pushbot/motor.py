import nengo

class Motor(nengo.Node):
    def __init__(self, bot, label='motor'):
        self.bot = bot
        super(Motor, self).__init__(self.motor_output, size_in=2,
                                     label=label)

    def motor_output(self, t, x):
        if self.bot is not None:
            self.bot.motor(x[0], x[1])
