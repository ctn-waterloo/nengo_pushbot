import nengo

try:
    import nengo_spinnaker
except ImportError:
    nengo_spinnaker = None


class Tracks(nengo.Node):

    def __init__(self, bot, label='tracks'):
        self.bot = bot
        super(Tracks, self).__init__(output=self.motor_output, size_in=2,
                                     label=label)

    def motor_output(self, t, x):
        if self.bot is not None:
            self.bot.send_motor(x[0], x[1])
        return []

    def spinnaker_build(self, builder):
        import nengo_spinnaker.filter_vertex
        self.vertex = nengo_spinnaker.filter_vertex.FilterVertex(
            dimensions=2, output_id=1, output_period=10, label=self.label)
        builder.add_vertex(self.vertex)

        bot_vertex = self.bot.get_bot_vertex(builder)
        bot_edge = nengo_spinnaker.edges.NengoEdge(2, self.vertex,
            bot_vertex, filter_is_accumulatory=False)
        builder.add_edge(bot_edge)



#inform nengo_spinnaker that this Node should be handled specially
if nengo_spinnaker is not None:
    import nengo_spinnaker.builder
    import nengo_spinnaker.edges
    @nengo_spinnaker.builder.register_build_edge(pre=nengo.Ensemble,
                                                 post=Tracks)
    def spinnaker_build_edge_in(builder, c):
        prevertex = builder.ensemble_vertices[c.pre]
        edge = nengo_spinnaker.edges.DecoderEdge(c, prevertex, c.post.vertex)
        edge.index = prevertex.decoders.get_decoder_index(edge)
        c.post.vertex.filters.add_edge(edge)
        return edge
