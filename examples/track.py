# detect lights at different frequencies
# if you see a dot too low, back up (otherwise go forward)

import nengo_pushbot

import nengo

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.47')
    bot.track_freqs([200, 100])
    bot.laser(200)
    bot.show_image()

    pos0 = nengo.Ensemble(100, 2, label='pos0')
    nengo.Connection(bot.tracker_0, pos0)

    pos1 = nengo.Ensemble(100, 2, label='pos1')
    nengo.Connection(bot.tracker_1, pos1)

    def orient(x):
        if x[1] < 0:
            return [-1, 1]
        else:
            return [1, -1]

    nengo.Connection(pos1, bot.motor, function=orient, transform=0.05,
                     synapse=0.002)
    nengo.Probe(pos1)
    nengo.Probe(pos0)

if __name__ == '__main__':
    sim = nengo.Simulation(model)
    sim.run(1000)
