import numpy as np
import nengo_spinnaker.assembler
import nengo_spinnaker.utils


class CompassVertex(nengo_spinnaker.utils.vertices.NengoVertex):
    """Application to provide calibrated compass data."""
    MODEL_NAME = 'pushbot_compass_calibrate'
    MAX_ATOMS = 1
    size_in = 3

    def __init__(self):
        super(CompassVertex, self).__init__(1)
        self.regions = [None, None, None]

    @classmethod
    def get_output_keys_region(cls, cv, assembler):
        output_keys = list()

        for c in assembler.get_outgoing_connections(cv):
            for d in range(c.width):
                output_keys.append(c.keyspace.key(d=d))

        return nengo_spinnaker.utils.vertices.UnpartitionedListRegion(
            output_keys)

    @classmethod
    def get_transform(cls, cv, assembler):
        # Combine the outgoing connections
        conns = nengo_spinnaker.utils.connections.Connections(
            assembler.get_outgoing_connections(cv))

        for tf in conns.transforms_functions:
            assert tf.function is None

        transforms = np.vstack(t.transform for t in
                               conns.transforms_functions)
        transform_region =\
            nengo_spinnaker.utils.vertices.UnpartitionedMatrixRegion(
                transforms, formatter=nengo_spinnaker.utils.fp.bitsk)

        return transforms.shape[0], transform_region

    @classmethod
    def assemble(cls, cv, assembler):
        # Create the output keys region and add it to the instance, then
        # return.
        size_out, cv.regions[2] = cls.get_transform(cv, assembler)
        cv.regions[1] = cls.get_output_keys_region(cv, assembler)

        # Create the system region
        cv.regions[0] =\
            nengo_spinnaker.utils.vertices.UnpartitionedListRegion(
                [size_out])

        return cv

nengo_spinnaker.assembler.Assembler.register_object_builder(
    CompassVertex.assemble, CompassVertex)
