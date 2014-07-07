import nengo
import nengo_pushbot

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.49')
    bot.show_image()

if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run(1000)






