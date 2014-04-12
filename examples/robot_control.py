import nengo

import nengo_pushbot as pushbot
import numpy as np

bot = pushbot.PushBot('10.162.177.45')

model = nengo.Network()
with model:
    input = nengo.Node(lambda t: [0.5*np.sin(t), 0.5*np.cos(t)])
    a = nengo.Ensemble(nengo.LIF(100), dimensions=2)
    motor = pushbot.Tracks(bot)
    nengo.Connection(input, a, filter=None)
    nengo.Connection(a, motor, filter=0.01)

sim_normal = nengo.Simulator(model)
sim_normal.run(100)

#import nengo_spinnaker
#sim = nengo_spinnaker.Simulator(model)
#sim.run(10)

