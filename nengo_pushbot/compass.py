import nengo

class Compass(nengo.Node):
    def __init__(self, bot, label='compass'):
        self.bot = bot
        super(Compass, self).__init__(self.compass_input, size_out=3,
                                     label=label)

    def compass_input(self, t):
        if self.bot is not None:
            return self.bot.get_compass()
        else:
            return [0, 0, 0]
