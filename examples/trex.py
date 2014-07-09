import nengo
import nengo_pushbot
import numpy as np

    
spinnaker = False



model = nengo.Network(label='pushbot')
with model:
    def inv(x):
        return -x

    # def sum_inp(x):
    #     return x[0]+x[1]

    if spinnaker:
        bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    else:
        #pass
        bot = nengo_pushbot.PushBotNetwork('10.162.177.55')
        bot.bot.show_image(decay=0.5)
    
    kb_input = nengo.Node([0, 0, 0, 0], label='keyboard')
    sum_left = nengo.Ensemble(100, dimensions=1, label='sum_left')
    sum_right = nengo.Ensemble(100, dimensions=1, label='sum_right')
    invert_pop = nengo.Ensemble(100, dimensions=1, label='invert')
    left_drive = nengo.Ensemble(100, dimensions=1, label='left_drive')
    right_drive = nengo.Ensemble(100, dimensions=1, label='right_drive')

    # Get turn component
    nengo.Connection(kb_input[2], invert_pop, function=inv)

    # Get forward component
    nengo.Connection(kb_input[3], sum_left)
    nengo.Connection(kb_input[2],  sum_left, transform=0.5)
    nengo.Connection(kb_input[3],  sum_right)
    nengo.Connection(invert_pop,  sum_right, transform=0.5)

    # Bind sums to output
    nengo.Connection(sum_left, left_drive)
    nengo.Connection(sum_right, right_drive)    

    nengo.Connection(left_drive, bot.motor[0], synapse=0.01, transform=0.5)
    nengo.Connection(right_drive, bot.motor[1], synapse=0.01, transform=0.5)
    #nengo.Probe(a)


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