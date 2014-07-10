import nengo
import nengo_pushbot

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    bot.count_spikes(left=(0, 0, 64, 128), right=(64, 0, 128, 128))

    a = nengo.Ensemble(100, 2)
    nengo.Connection(bot.count_left, a[0])
    nengo.Connection(bot.count_right, a[1])

    p = nengo.Probe(bot.count_left, synapse=0.05)

import nengo_spinnaker
sim = nengo_spinnaker.Simulator(model)
sim.run(30.)

from matplotlib import pyplot as plt
plt.plot(sim.trange(), sim.data[p])
plt.ylim([0, 1.])
plt.show(block=True)
