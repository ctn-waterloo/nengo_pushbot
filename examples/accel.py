# orient to a particular direction
# also plot the accelerometer data

import nengo_pushbot
import nengo


model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.49')

    accel = nengo.Ensemble(300, 3, radius=2)
    nengo.Connection(bot.accel, accel)

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
    nengo.Probe(accel)
    #nengo.Probe(direction, 'spikes')


if __name__ == '__main__':
    #import nengo_gui
    #jv = nengo_gui.javaviz.View(model)
    sim = nengo.Simulator(model)
    #jv.update_model(sim)
    #jv.view()

    while True:
        sim.run(100)

