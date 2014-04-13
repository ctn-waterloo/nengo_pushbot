import nengo
import nengo_pushbot

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.45')


view = nengo_pushbot.RetinaView(bot.bot)

sim = nengo.Simulator(model)
sim.run(1000)






