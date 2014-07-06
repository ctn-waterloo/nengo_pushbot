import nengo

class Beep(nengo.Node):
    def __init__(self, bot, label='beep'):
        self.bot = bot
        super(Beep, self).__init__(self.beep_output, size_in=1,
                                     label=label)

    def beep_output(self, t, x):
        if self.bot is not None:
            self.bot.beep(x[0])
