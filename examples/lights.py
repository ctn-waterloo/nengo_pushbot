# turn on laser and leds


import nengo
import nengo_pushbot

model = nengo.Network()
with model:
    bot = nengo_pushbot.PushBotNetwork('10.162.177.49')
    bot.laser(100)  # set laser to 100Hz
    bot.led(5)      # set led to 5Hz

if __name__ == '__main__':
    sim = nengo.Simulator(model)
    sim.run(1000)






