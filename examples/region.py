import nengo_pushbot

import nengo

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.49')
    bot.count_spikes(all=(0,0,128,128))

    count = nengo.Ensemble(100, 1, radius=200)
    nengo.Connection(bot.count_all, count)

    nengo.Probe(count)


if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run()
