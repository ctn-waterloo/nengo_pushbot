import nengo_pushbot

import nengo

bot = nengo_pushbot.PushBot3('10.162.177.51')
import time
time.sleep(2)
bot.activate_sensor('compass', freq=10)

model = nengo.Network()
with model:
    bot_compass = nengo.Node(lambda t: bot.get_compass(), size_out=3)

    direction = nengo.Ensemble(100, 2)
    nengo.Connection(bot_compass[1:], direction)

    nengo.Probe(direction)
    nengo.Probe(direction, 'spikes')

import nengo_gui
jv = nengo_gui.javaviz.View(model)
sim = nengo.Simulator(model)
jv.update_model(sim)
jv.view()

while True:
    sim.run(100)

