import nengo_pushbot

import nengo

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.55')

    direction = nengo.Ensemble(100, 2)

    nengo.Connection(bot.compass[1:], direction)

    def orient(x):
        target = [0, 1]
        dot = -x[0]*target[1] + x[1]*target[0]
        if dot > 0:
            return [1, -1]
        else:
            return [-1, 1]

    nengo.Connection(direction, bot.motor, function=orient, transform=0.2)
    nengo.Probe(direction)
