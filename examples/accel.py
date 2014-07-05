import nengo_pushbot

import nengo

bot = nengo_pushbot.PushBot3.get_bot('10.162.177.55')

import time
time.sleep(2)
bot.activate_sensor('compass', freq=100)
bot.activate_sensor('accel', freq=100)

model = nengo.Network()
with model:
    bot_compass = nengo.Node(lambda t: bot.get_compass(), size_out=3, label='bot compass')
    bot_accel = nengo.Node(lambda t: bot.get_accel(), size_out=3, label='bot accel')

    accel = nengo.Ensemble(300, 3, radius=2)
    nengo.Connection(bot_accel, accel)

    direction = nengo.Ensemble(100, 2)
    nengo.Connection(bot_compass[1:], direction)

    bot_motor = nengo.Node(lambda t, x: bot.motor(*x), size_in=2)

    def orient(x):
        target = [0, 1]
        dot = -x[0]*target[1] + x[1]*target[0]
        if dot > 0:
            return [1, -1]
        else:
            return [-1, 1]

    nengo.Connection(direction, bot_motor, function=orient, transform=0.2)


    nengo.Probe(direction)
    nengo.Probe(accel)
    #nengo.Probe(direction, 'spikes')

#import nengo_gui
#jv = nengo_gui.javaviz.View(model)
#sim = nengo.Simulator(model)
#jv.update_model(sim)
#jv.view()

#while True:
#    sim.run(100)

