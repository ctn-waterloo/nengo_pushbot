import nengo

import nengo_spinnaker



#@nengo_spinnaker.custom_build
class Tracks(nengo.Node):

    def __init__(self, bot, label='tracks'):
        self.bot = bot
        super(Tracks, self).__init__(output=self.motor_output, size_in=2,
                                     label=label)

    def motor_output(self, t, x):
        self.bot.send_motor(x[0], x[1])
        return []



from nengo.builder import _builder_func_dict as bfd
bfd[Tracks] = bfd[nengo.Node]
