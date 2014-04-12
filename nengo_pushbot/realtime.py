import time
class Realtime(object):
    def __init__(self, scale=1.0):
        self.scale = 1.0 / scale
        self.start = None
    def update(self, t):
        if self.start is None:
            self.start = time.time()
        now = time.time()
        while now - self.start < t * self.scale:
            now = time.time()
        return []
