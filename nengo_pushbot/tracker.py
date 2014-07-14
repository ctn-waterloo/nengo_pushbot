import nengo

class Tracker(nengo.Node):
    def __init__(self, bot, index):
        self.bot = bot
        self.index = index
        super(Tracker, self).__init__(self.tracker_input, size_out=3,
                                     label='tracker_%d' % index)

    def tracker_input(self, t):
        if self.bot is not None:
            return (self.bot.p_x[self.index]/64.0 - 1,
                    self.bot.p_y[self.index]/64.0 - 1,
                    min(self.bot.track_certainty[self.index], 1.0))
        else:
            return [0, 0, 0]
