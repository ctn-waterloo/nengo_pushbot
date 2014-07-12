# detect lights at different frequencies
# if you see a dot too low, back up (otherwise go forward)

import nengo_pushbot
import nengo

spinnaker = True

model = nengo.Network()
with model:
    if not spinnaker:
        bot = nengo_pushbot.PushBotNetwork('10.162.177.49')
    else:
        bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    bot.track_freqs([200])
    bot.laser(200)
    bot.led(200)
    bot.show_image()

    pos0 = nengo.Ensemble(100, 2, label='pos0')
    nengo.Connection(bot.tracker_0, pos0)

    #pos1 = nengo.Ensemble(100, 2, label='pos1')
    #nengo.Connection(bot.tracker_1, pos1)

    def orient(x):
        if x[1] < 0:
            return [-1, 1]
        else:
            return [1, -1]

    #nengo.Connection(pos1, bot.motor, function=orient, transform=0.05,
    #                 synapse=0.002)
    #nengo.Probe(pos1)
    p0 = nengo.Probe(bot.tracker_0, synapse=0.01)
    p1 = nengo.Probe(pos0, synapse=0.01)

if __name__ == '__main__':
    if spinnaker:
        import nengo_spinnaker
        sim = nengo_spinnaker.Simulator(model)
        sim.run(10, clean=False)
    else:
        sim = nengo.Simulator(model)
        while True:
            sim.run(100)

import pylab
pylab.subplot(2,1,1)
pylab.plot(sim.data[p0])
pylab.subplot(2,1,2)
pylab.plot(sim.data[p1])
pylab.show()
