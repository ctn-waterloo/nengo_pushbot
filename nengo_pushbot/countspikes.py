import nengo

class CountSpikes(nengo.Node):
    def __init__(self, bot, key, region):
        self.bot = bot
        self.key = key
        self.region = region
        super(CountSpikes, self).__init__(self.count_input, size_out=1,
                                     label='count_%s' % key)

    def count_input(self, t):
        if self.bot is not None:
            return self.bot.get_spike_rate(self.key)
        else:
            return 0
