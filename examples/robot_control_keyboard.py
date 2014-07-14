# control the motors of the robot
# also contains code for connecting to SpiNNaker



import nengo

spinnaker = False

import nengo_pushbot
import numpy as np

model = nengo.Network(label='pushbot')
with model:
    input = nengo.Node([0,0], label='keyboard')
    #a = nengo.Ensemble(500, dimensions=2, label='a')

    if spinnaker:
        bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    else:
        bot = nengo_pushbot.PushBotNetwork('10.162.177.49')
        bot.show_image()

    nengo.Connection(input, bot.motor, synapse=0.01, transform=[[-1, -1], [-0.3, 0.3]])


if __name__ == '__main__':
    import nengo_gui.javaviz
    jv = nengo_gui.javaviz.View(model)

    if spinnaker:
        import nengo_spinnaker

        config = nengo_spinnaker.Config()
        config[input].f_of_t = True
        config[input].f_period = 2*np.pi

        sim = nengo_spinnaker.Simulator(model)
    else:
        sim = nengo.Simulator(model)
    jv.update_model(sim)
    jv.view()

    sim.run(5000)

    #import nengo_spinnaker
    #sim = nengo_spinnaker.Simulator(model)
    #sim.run(10)

