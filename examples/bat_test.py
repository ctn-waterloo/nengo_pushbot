import nengo_pushbot
import nengo


model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.43')
    bot.bot.activate_sensor('bat', freq=10)

    bat = nengo.Ensemble(100, 1)

    bat_level=nengo.Node(lambda t: bot.bot.sensor['bat'])

    nengo.Connection(bat_level, bat)

    def orient(x):
        target = [0, 1]
        dot = -x[0]*target[1] + x[1]*target[0]
        if dot > 0:
            return [1, -1]
        else:
            return [-1, 1]


    nengo.Probe(bat)




import nengo_gui
gui = nengo_gui.Config()
gui[model].scale = 2.2454948153701624
gui[model].offset = 535.0607723451053,381.2466437329056
gui[bat].pos = 141.765, 153.095
gui[bat].scale = 1.000
gui[bat_level].pos = 17.933, 182.577
gui[bat_level].scale = 1.000
gui[bot].pos = 3.074, -50.801
gui[bot].scale = 1.000
gui[bot].size = 94.679, 213.603
gui[bot.compass].pos = 0.000, 0.000
gui[bot.compass].scale = 1.000
gui[bot.motor].pos = 10.413, -101.603
gui[bot.motor].scale = 1.000
gui[bot.accel].pos = 0.000, 0.000
gui[bot.accel].scale = 1.000
gui[bot.beep].pos = 0.000, 0.000
gui[bot.beep].scale = 1.000
gui[bot.gyro].pos = 0.000, 0.000
gui[bot.gyro].scale = 1.000
gui[bot.touch].pos = 0.000, 0.000
gui[bot.touch].scale = 1.000
