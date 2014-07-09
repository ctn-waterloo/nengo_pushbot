import nengo

import nengo_pushbot
import numpy as np

bot1 = nengo_pushbot.PushBot2('10.162.177.51', port=56000, message_delay=0.01)
bot1.laser(freq=155)
bot1.led(freq=155)

model = nengo.Network(label='pushbot')
with model:
    #bot = nengo_pushbot.PushBot2('ctndroid.uwaterloo.ca', port=56043, message_delay=0.01)
    bot = nengo_pushbot.PushBot2('10.162.177.49', port=56000, message_delay=0.01)
    bot.laser(freq=0)
    motor1 = nengo.Node([0, 0], label='motor1')
    bot_motor1 = nengo.Node(lambda t, x: bot1.motor(x[0], x[1]), size_in=2, label='motor1')
    nengo.Connection(motor1, bot_motor1, synapse=0.01, transform=[[1, 1], [1, -1]])

    motor = nengo.Node([0, 0], label='motor')
    bot_motor = nengo.Node(lambda t, x: bot.motor(x[0], x[1]), size_in=2, label='motor')
    nengo.Connection(motor, bot_motor, synapse=0.01, transform=[[1, 1], [1, -1]])

    blink = nengo_pushbot.BlinkTracker(bot.socket, freqs=[155])
    #view = nengo_pushbot.view.RetinaView(blink)
    pos1 = nengo.Node(lambda t: [blink.p_x[0]/64-1, blink.p_y[0]/64-1], label='blink1')
    blink_pos1 = nengo.Ensemble(200, 2, radius=1.5, label='blink_pos1')
    nengo.Connection(pos1, blink_pos1)

    blink_certainty = nengo.networks.EnsembleArray(100, 1, label='blink_certainty')
    c = nengo.Node(lambda t: min(blink.certainty()*100, 1))
    nengo.Connection(c, blink_certainty.input)

    nengo.Probe(blink_pos1)
    nengo.Probe(blink_certainty.output)

    def control_func(x):
        yy, xx = x
        #if c < 0.1: return 0.5
        if yy < -0.1: return -0.3
        if yy > 0.1: return 0.3
        return 0
    control = nengo.Ensemble(200, 2, radius=1.5)
    #nengo.Connection(blink_certainty.output, control[2])
    nengo.Connection(blink_pos1, control[:2])
    nengo.Connection(control, bot_motor,  function=control_func, transform=[[-1], [1]])

    #laser = nengo.Node([0], label='laser')
    #bot_laser = nengo.Node(lambda t, x: bot.laser(x[0]*10), size_in=1, label='laser')
    #nengo.Connection(laser, bot_laser, synapse=0.01)

import nengo_gui.javaviz
jv = nengo_gui.javaviz.View(model)

sim_normal = nengo.Simulator(model)
jv.update_model(sim_normal)
jv.view()

sim_normal.run(5000)

