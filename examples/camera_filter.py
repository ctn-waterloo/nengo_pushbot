import nengo
import nengo_pushbot

import numpy as np

class PulseBot(nengo_pushbot.PushBot):
    def __init__(self, address, port=56000, message_delay=0.01):
        super(PulseBot, self).__init__(address, port, message_delay)
        self.view2 = np.zeros((128, 128), dtype=float)
        self.last_spike = np.zeros((128, 128), dtype=int)

    def update_sensors(self, t):
        super(PulseBot, self).update_sensors()

        decay = np.exp(-0.001/0.03)
        self.view2 = self.view2*decay + (1-decay)*self.view

        diff = self.last_spike[data_x, data_y]
        self.last_spike[data_x, data_y] = self.tick
        return []


class PulseView(nengo_pushbot.RetinaView):
    def get_image(self):
        return self.bot.view2
    def get_image_range(self):
        return -0.1, 0.1


model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.45', bot_class=PulseBot)



view = PulseView(bot.bot)

sim = nengo.Simulator(model)
sim.run(100000)






