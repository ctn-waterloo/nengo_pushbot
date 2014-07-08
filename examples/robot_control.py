import nengo

spinnaker = False

import nengo_pushbot
import numpy as np

model = nengo.Network(label='pushbot')
with model:
    input = nengo.Node(lambda t: [0.5*np.sin(t), 0.5*np.cos(t)], label='input')
    a = nengo.Ensemble(100, dimensions=2, label='a')

    if spinnaker:
        bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    else:
        bot = nengo_pushbot.PushBotNetwork('10.162.177.49')

    nengo.Connection(input, a, synapse=None)
    nengo.Connection(a, bot.motor, synapse=0.01, transform=0.1)
    nengo.Probe(a)


if __name__ == '__main__':
    #import nengo_gui.javaviz
    #jv = nengo_gui.javaviz.View(model)

    if spinnaker:
        import nengo_spinnaker

        config = nengo_spinnaker.Config()
        config[input].f_of_t = True
        config[input].f_period = 2*np.pi

        sim = nengo_spinnaker.Simulator(model)
    else:
        sim = nengo.Simulator(model)
    #jv.update_model(sim_normal)
    #jv.view()

    sim.run(5000)

    #import nengo_spinnaker
    #sim = nengo_spinnaker.Simulator(model)
    #sim.run(10)

