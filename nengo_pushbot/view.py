import numpy as np
import thread

class RetinaView(object):
    def __init__(self, bot):
        self.bot = bot
        thread.start_new_thread(self.update_loop, ())

    def get_image(self):
        img = self.bot.image
        self.bot.clear_image()
        return img
    def get_image_range(self):
        return -1, 1

    def update_loop(self):
        import pylab
        pylab.ion()
        vmin, vmax = self.get_image_range()
        self.img = pylab.imshow(self.bot.image, vmin=vmin, vmax=vmax,
                                cmap='gray', interpolation='none')
        while True:
            self.img.set_data(self.get_image())
            pylab.draw()
            #pylab.pause(0.001)
