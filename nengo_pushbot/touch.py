import nengo

class Touch(nengo.Node):
    def __init__(self, bot, label='touch'):
        self.bot = bot
        super(Touch, self).__init__(self.touch_input, size_out=1,
                                     label=label)

    def touch_input(self, t):
        if self.bot is not None:
            return self.bot.get_touch()
        else:
            return 0
