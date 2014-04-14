import nengo

import nengo_pushbot
import numpy as np

model = nengo.Network()
with model:
    #input = nengo.Node(lambda t: [0.5*np.sin(10*t), 0.5*np.cos(10*t)])

    input = nengo.Node([0.5, -0.5])
    a = nengo.Ensemble(nengo.LIF(100), dimensions=2)
    b = nengo.Ensemble(nengo.LIF(100), dimensions=2)
    c = nengo.Ensemble(nengo.LIF(100), dimensions=2)
    d = nengo.Ensemble(nengo.LIF(100), dimensions=2)

    #nengo.Connection(a, b, filter=0.01)
    #nengo.Connection(b, c, filter=0.01)
    #nengo.Connection(c, d, filter=0.01)

    #nengo.Connection(a, a, transform=[[1.1, 0], [0, 1.1]], filter=0.1)
    #b = nengo.Ensemble(nengo.LIF(100), dimensions=2)

    bot = nengo_pushbot.PushBot(address=(0xFE, 0xFF, 1, 0, 0))

    tracks = nengo_pushbot.Tracks(bot)
    #def printout(t, x):
    #    print t, x
    #    return []
    #tracks2 = nengo.Node(printout, size_in=2)

    nengo.Connection(input, a, filter=0.01)
    nengo.Connection(a, b, filter=0.01)
    nengo.Connection(b, c, filter=0.01)
    nengo.Connection(c, d, filter=0.01)
    nengo.Connection(d, tracks, filter=0.01)
    #nengo.Connection(b, tracks2, filter=0.01)

#sim_normal = nengo.Simulator(model)
#sim_normal.run(5)

import nengo_spinnaker
sim = nengo_spinnaker.Simulator(model)
sim.run(10)

