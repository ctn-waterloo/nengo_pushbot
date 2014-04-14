import nengo

import nengo_pushbot
import numpy as np

model = nengo.Network()
with model:
    input = nengo.Node(lambda t: [0.5*np.sin(t), 0.5*np.cos(t)])
    a = nengo.Ensemble(nengo.LIF(100), dimensions=2)

    bot = nengo_pushbot.PushBotNetwork('10.162.177.45', message_delay=0.001)

    nengo.Connection(input, a, filter=None)
    nengo.Connection(a, bot.tracks, filter=0.01)

sim_normal = nengo.Simulator(model)
sim_normal.run(5000)

#import nengo_spinnaker
#sim = nengo_spinnaker.Simulator(model)
#sim.run(10)

