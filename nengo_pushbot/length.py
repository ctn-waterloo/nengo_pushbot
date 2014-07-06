import nengo.spa as spa

vocab = spa.Vocabulary(512)

data = []
for i in range(100):
    data.extend(vocab.parse('A%d' % i).v)

import pylab
pylab.hist(data, 50)
pylab.show()
