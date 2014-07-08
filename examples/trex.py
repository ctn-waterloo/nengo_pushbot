import nengo
import nengo_pushbot
import numpy as np

    
spinnaker = False



model = nengo.Network(label='pushbot')
with model:
    input = nengo.Node(lambda t: [0.5*np.sin(t), 0.5*np.cos(t)], label='input')
    a = nengo.Ensemble(100, dimensions=2, label='a', radius=200)

    if spinnaker:
        bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    else:
        bot = nengo_pushbot.PushBotNetwork('10.162.177.43')
        bot.bot.show_image(decay=0.5)

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








import nengo_gui
gui = nengo_gui.Config()
gui[model].scale = 1.2868750026997895
gui[model].offset = 90.94158997498869,-26.8225001187908
gui[a].pos = 175.000, 250.000
gui[a].scale = 1.000
gui[input].pos = 50.000, 250.000
gui[input].scale = 1.000
gui[bot].pos = 350.000, 250.000
gui[bot].scale = 1.000
gui[bot].size = 109.750, 412.000
gui[bot.motor].pos = 350.000, 100.000
gui[bot.motor].scale = 1.000
gui[bot.accel].pos = 350.000, 175.000
gui[bot.accel].scale = 1.000
gui[bot.beep].pos = 350.000, 250.000
gui[bot.beep].scale = 1.000
gui[bot.compass].pos = 350.000, 325.000
gui[bot.compass].scale = 1.000
gui[bot.gyro].pos = 350.000, 400.000
gui[bot.gyro].scale = 1.000
