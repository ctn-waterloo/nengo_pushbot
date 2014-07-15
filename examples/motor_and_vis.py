import nengo
import nengo_pushbot
import numpy as np
    
spinnaker = False

model = nengo.Network(label='pushbot')
with model:
    def inv(x):
        return -x

    if spinnaker:
        bot = nengo_pushbot.PushBotNetwork('1,0,EAST')
    else:
        bot = nengo_pushbot.PushBotNetwork('10.162.177.57')
        bot.bot.show_image(decay=0.5)        
    
    # keyboard input 
    kb_input = nengo.Node([0, 0, 0, 0], label='keyboard')
    invert_pop = nengo.Ensemble(100, dimensions=1, label='invert')
    left_drive = nengo.Ensemble(100, dimensions=1, label='left_drive')
    right_drive = nengo.Ensemble(100, dimensions=1, label='right_drive')
    
    # Get turn component
    nengo.Connection(kb_input[2], invert_pop, function=inv)

    # Set up motor drives
    #   Forward / backward
    nengo.Connection(kb_input[3],  left_drive)
    nengo.Connection(kb_input[3],  right_drive)
    #   Left / right
    nengo.Connection(kb_input[2],  left_drive, transform=0.3)
    nengo.Connection(invert_pop,   right_drive, transform=0.3)

    # Connect drive populations to the motors
    nengo.Connection(left_drive,  bot.motor[0], synapse=0.01, transform=-0.5)
    nengo.Connection(right_drive, bot.motor[1], synapse=0.01, transform=-0.5)

    # Visualize motor drives
    nengo.Probe(left_drive)
    nengo.Probe(right_drive)


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