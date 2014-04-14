import nengo
import nengo_pushbot

class PushBotNetwork(nengo.Network):
    def __init__(self, address, port=56000, message_delay=0.01,
                 sensors=True, realtime=True,
                 bot_class=nengo_pushbot.PushBot):
        self.bot = bot_class(address, port=port,
                             message_delay=message_delay)
        self.tracks = nengo_pushbot.Tracks(self.bot, label='tracks')

        if sensors:
            print self.bot
            print self.bot.update_sensors
            self.update = nengo.Node(self.bot.update_sensors)

        if realtime:
            self.realtime = nengo.Node(nengo_pushbot.Realtime().update)
