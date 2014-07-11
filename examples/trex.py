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
        bot = nengo_pushbot.PushBotNetwork('10.162.177.47')
        bot.bot.show_image(decay=0.5)
        
    
    # keyboard input 
    kb_input = nengo.Node([0, 0, 0, 0], label='keyboard')
    sum_left = nengo.Ensemble(100, dimensions=1, label='sum_left')
    sum_right = nengo.Ensemble(100, dimensions=1, label='sum_right')
    invert_pop = nengo.Ensemble(100, dimensions=1, label='invert')
    left_drive = nengo.Ensemble(100, dimensions=1, label='left_drive')
    right_drive = nengo.Ensemble(100, dimensions=1, label='right_drive')
    
    #track laser to control forward and backward movement
    bot.track_freqs([300], sigma_p=60)
    bot.laser(300)    
    pos = nengo.Ensemble(30, 1, label='pos')
    nengo.Connection(bot.tracker_0[0], pos)

    # signs of the return [1 , 1] debending on B or F robot version
    def move(x):
        if x[0] > 0.5:
            return [-1, -1]
        else:
            return [1, 1]

    nengo.Connection(pos, bot.motor, function=move, transform=0.2)
    nengo.Probe(pos)

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

import nengo_gui
gui = nengo_gui.Config()
gui[model].scale = 1.1550143735792258
gui[model].offset = 519.6294921957826,502.4417682323084
gui[sum_left].pos = -160.834, -391.160
gui[sum_left].scale = 1.000
gui[sum_right].pos = -212.325, -90.920
gui[sum_right].scale = 1.000
gui[invert_pop].pos = -288.257, -213.772
gui[invert_pop].scale = 1.000
gui[left_drive].pos = -153.570, -289.420
gui[left_drive].scale = 1.000
gui[right_drive].pos = -235.737, 25.199
gui[right_drive].scale = 1.000
gui[pos].pos = -57.013, -66.097
gui[pos].scale = 1.000
gui[kb_input].pos = -8.850, -218.245
gui[kb_input].scale = 1.000
gui[bot].pos = 660.479, 715.642
gui[bot].scale = 1.000
gui[bot].size = 191.094, 258.348
gui[bot.tracker_0].pos = 623.510, 642.468
gui[bot.tracker_0].scale = 1.000
gui[bot.motor].pos = 698.307, 788.816
gui[bot.motor].scale = 1.000
gui[bot.accel].pos = 698.307, 788.816
gui[bot.accel].scale = 1.000
gui[bot.beep].pos = 698.307, 788.816
gui[bot.beep].scale = 1.000
gui[bot.compass].pos = 698.307, 788.816
gui[bot.compass].scale = 1.000
gui[bot.gyro].pos = 698.307, 788.816
gui[bot.gyro].scale = 1.000
gui[bot.touch].pos = 698.307, 788.816
gui[bot.touch].scale = 1.000
