import nengo

import nengo_pushbot
import numpy as np

model = nengo.Network(label='pushbot')
with model:
    bot = nengo_pushbot.PushBot2('ctndroid.uwaterloo.ca', port=56043, message_delay=0.01)
    bot.laser(freq=70)

    motor = nengo.Node([0, 0], label='motor')
    bot_motor = nengo.Node(lambda t, x: bot.motor(x[0], x[1]), size_in=2, label='motor')
    nengo.Connection(motor, bot_motor, synapse=0.01)

    beep = nengo.Node([0], label='beep')
    bot_beep = nengo.Node(lambda t, x: bot.beep(x[0]*15000), size_in=1, label='beep')
    nengo.Connection(beep, bot_beep, synapse=0.01)

    blink = nengo_pushbot.BlinkTracker(bot.socket, freq=100)
    pos = nengo.Node(lambda t: [blink.p_x/64-1, blink.p_y/64-1], label='blink')
    blink_pos = nengo.Ensemble(200, 2, radius=1.5, label='blink_pos')
    blink_certainty = nengo.Ensemble(100, 1, label='blink_certainty')
    c = nengo.Node(lambda t: blink.certainty()*1000)
    nengo.Connection(c, blink_certainty)
    nengo.Connection(pos, blink_pos)

    nengo.Probe(blink_pos)
    nengo.Probe(blink_certainty)

    #laser = nengo.Node([0], label='laser')
    #bot_laser = nengo.Node(lambda t, x: bot.laser(x[0]*10), size_in=1, label='laser')
    #nengo.Connection(laser, bot_laser, synapse=0.01)

import nengo_gui.javaviz
jv = nengo_gui.javaviz.View(model)

sim_normal = nengo.Simulator(model)
jv.update_model(sim_normal)
jv.view()

sim_normal.run(5000)

