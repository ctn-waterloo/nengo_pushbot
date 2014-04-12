import nengo
import nengo_pushbot
bot = nengo_pushbot.PushBot('10.162.177.45')

view = nengo_pushbot.RetinaView(bot)


model = nengo.Network()
with model:
    sensors = nengo.Node(bot.update_sensors)
    realtime = nengo.Node(nengo_pushbot.Realtime().update)


sim = nengo.Simulator(model)
sim.run(10)






