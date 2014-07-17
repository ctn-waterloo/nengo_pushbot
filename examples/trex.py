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
    sum_left = nengo.Ensemble(100, dimensions=1, label='sum_left')
    sum_right = nengo.Ensemble(100, dimensions=1, label='sum_right')
    invert_pop = nengo.Ensemble(100, dimensions=1, label='invert')
    left_drive = nengo.Ensemble(100, dimensions=1, label='left_drive')
    right_drive = nengo.Ensemble(100, dimensions=1, label='right_drive')
    
    #track laser to control forward and backward movement
    bot.track_freqs([400, 20])
    bot.laser(400)
    laser_pos = nengo.Ensemble(30, 1, label='laser_pos')
    food_pos = nengo.Ensemble(30, 1, label='food_pos')
    nengo.Connection(bot.tracker_0[0], laser_pos)
    nengo.Connection(bot.tracker_1[0], food_pos)

    # signs of the return [1 , 1] debending on B or F robot version
    def avoid_move(x):
        if x[0] > 0.5 and x[0]<0.6:
            return [-1, 1]
        elif x[0] > 0.6:
            return [-1, -1]
        else:
            return [0.5, 0.5]

    def hunt_move(x):
        if x[0] < -0.3:
            return [1, 1]            
        else:
            return [0, 0]        


    # Attach desires
    nengo.Connection(laser_pos, bot.motor, function=avoid_move, transform=-0.3)
    nengo.Connection(food_pos, bot.motor, function=hunt_move, transform=-0.8)
    nengo.Probe(laser_pos)
    nengo.Probe(food_pos)

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

    nengo.Connection(left_drive, bot.motor[0], synapse=0.01, transform=-0.5)
    nengo.Connection(right_drive, bot.motor[1], synapse=0.01, transform=-0.5)


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
gui[model].scale = 1.0359777933793948
gui[model].offset = 185.77345728723992,-45.05880826659211
gui[sum_left].pos = 400.000, 137.500
gui[sum_left].scale = 1.000
gui[sum_right].pos = 400.000, 212.500
gui[sum_right].scale = 1.000
gui[invert_pop].pos = 400.000, 287.500
gui[invert_pop].scale = 1.000
gui[left_drive].pos = 400.000, 362.500
gui[left_drive].scale = 1.000
gui[right_drive].pos = 400.000, 437.500
gui[right_drive].scale = 1.000
gui[laser_pos].pos = 400.000, 512.500
gui[laser_pos].scale = 1.000
gui[food_pos].pos = 400.000, 587.500
gui[food_pos].scale = 1.000
gui[kb_input].pos = 50.000, 362.500
gui[kb_input].scale = 1.000
gui[bot].pos = 225.000, 362.500
gui[bot].scale = 1.000
gui[bot].size = 124.875, 637.000
gui[bot.tracker_0].pos = 225.000, 100.000
gui[bot.tracker_0].scale = 1.000
gui[bot.tracker_1].pos = 225.000, 175.000
gui[bot.tracker_1].scale = 1.000
gui[bot.motor].pos = 225.000, 250.000
gui[bot.motor].scale = 1.000
gui[bot.accel].pos = 225.000, 325.000
gui[bot.accel].scale = 1.000
gui[bot.beep].pos = 225.000, 400.000
gui[bot.beep].scale = 1.000
gui[bot.compass].pos = 225.000, 475.000
gui[bot.compass].scale = 1.000
gui[bot.gyro].pos = 225.000, 550.000
gui[bot.gyro].scale = 1.000
gui[bot.touch].pos = 225.000, 625.000
gui[bot.touch].scale = 1.000
