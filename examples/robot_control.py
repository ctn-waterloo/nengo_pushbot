import nengo

import nengo_pushbot
import numpy as np

model = nengo.Network(label='pushbot')
with model:
    input = nengo.Node(lambda t: [0.5*np.sin(t), 0.5*np.cos(t)], label='input')
    a = nengo.Ensemble(100, dimensions=2, label='a')

    bot = nengo_pushbot.PushBotNetwork('10.162.177.49')

    nengo.Connection(input, a, synapse=None)
    nengo.Connection(a, bot.motor, synapse=0.01)
    nengo.Probe(a)

#import nengo_gui.javaviz
#jv = nengo_gui.javaviz.View(model)

#sim = nengo.Simulator(model)
#jv.update_model(sim_normal)
#jv.view()

#sim.run(5000)

#import nengo_spinnaker
#sim = nengo_spinnaker.Simulator(model)
#sim.run(10)

