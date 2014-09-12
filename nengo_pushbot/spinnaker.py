import numpy as np

from . import accel, beep, compass, countspikes, gyro, motor

try:
    import nengo_spinnaker

    import nengo_spinnaker.builder
    import pacman103.front.common

    def prepare_pushbot(objs, conns, probes):
        new_objs = list()
        new_conns = list()

        # Investigate the objects
        for obj in objs:
            if isinstance(obj, (motor.Motor, beep.Beep)):
                # Create a filter vertex between all incoming edges and the
                # object
                fv = nengo_spinnaker.builder.IntermediateFilter(
                    obj.size_in, transmission_period=100)
                new_objs.append(fv)

                in_conns = [c for c in conns if c.post is obj]
                for c in in_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                        from_connection(c)
                    c.post = fv
                    if isinstance(obj, beep.Beep):
                        c.transform *= 1000. / 2.**15  # Value to mHz
                    new_conns.append(c)

                # Get the robot vertex
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.bot, new_objs, new_conns)

                if isinstance(obj, motor.Motor):
                    # Add the motor enable/disable commands to the pushbot
                    # vertex
                    pushbot_vertex.start_packets.append(
                        nengo_spinnaker.assembler.MulticastPacket(
                            0, motor_keyspace(i=2, p=0, q=0, d=0).key(), 1))
                    pushbot_vertex.end_packets.append(
                        nengo_spinnaker.assembler.MulticastPacket(
                            0, motor_keyspace(i=2, p=0, q=0, d=0).key(), 0))

                    # Create a new connection from the multicast vertex to the
                    # pushbot vertex
                    new_conns.append(
                        nengo_spinnaker.utils.builder.IntermediateConnection(
                            mc_vertex, pushbot_vertex,
                            keyspace=motor_keyspace(i=2, p=0, q=0, d=0)))
                elif isinstance(obj, beep.Beep):
                    # Ensure that the beep is switched off
                    ks = pwm_keyspace(i=36, p=0)

                    pushbot_vertex.end_packets.append(
                        nengo_spinnaker.assembler.MulticastPacket(0, ks.key(),
                                                                  0))
                    new_conns.append(
                        nengo_spinnaker.utils.builder.IntermediateConnection(
                            mc_vertex, pushbot_vertex, keyspace=ks(d=0)))

                # Create a new connection between the filter vertex and the
                # pushbot
                if isinstance(obj, motor.Motor):
                    c = nengo_spinnaker.utils.builder.IntermediateConnection(
                        fv, pushbot_vertex,
                        keyspace=motor_keyspace(i=32, p=0, q=1),
                        transform=np.eye(2) * 100. / 2.**15)
                elif isinstance(obj, beep.Beep):
                    c = nengo_spinnaker.utils.builder.IntermediateConnection(
                        fv, pushbot_vertex, keyspace=pwm_keyspace(i=36, p=0))
                new_conns.append(c)

            elif isinstance(obj, (accel.Accel, gyro.Gyro)):
                # Ensure the appropriate sensor is activated, then provide the
                # appropriate edge from the pushbot vertex to the targets of
                # the objects
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.bot, new_objs, new_conns)


                # Add commands to enable appropriate sensors
                ks = generic_robot_keyspace(i=1, f=1, d=2)
                if isinstance(obj, accel.Accel):
                    pushbot_vertex.start_packets.append(
                        nengo_spinnaker.assembler.MulticastPacket(0, ks.key(),
                                                                  8 << 27 | 100
                                                                  )
                    )
                elif isinstance(obj, gyro.Gyro):
                    pushbot_vertex.start_packets.append(
                        nengo_spinnaker.assembler.MulticastPacket(0, ks.key(),
                                                                  7 << 27 | 100
                                                                  )
                    )
                c = nengo_spinnaker.utils.builder.IntermediateConnection(
                    mc_vertex, pushbot_vertex, keyspace=ks)
                new_conns.append(c)

                # Modify connections from this object to have their pre as the
                # pushbot vertex and their keys as the appropriate form
                out_conns = [c for c in conns if c.pre is obj]

                fv = nengo_spinnaker.builder.IntermediateFilter(3)
                if isinstance(obj, accel.Accel):
                    c = nengo_spinnaker.utils.builder.IntermediateConnection(
                        pushbot_vertex, fv, synapse=None,
                        keyspace=inbound_keyspace(i=1, s=8),
                        is_accumulatory=False)
                elif isinstance(obj, gyro.Gyro):
                    c = nengo_spinnaker.utils.builder.IntermediateConnection(
                        pushbot_vertex, fv, synapse=None,
                        keyspace=inbound_keyspace(i=1, s=7),
                        is_accumulatory=False)
                new_objs.append(fv)
                new_conns.append(c)

                for conn in out_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                        from_connection(conn)
                    if isinstance(obj, accel.Accel):
                        c.transform *= 40.
                    elif isinstance(obj, gyro.Gyro):
                        c.transform *= 100.
                    c.pre = fv

                    new_conns.append(c)

            elif isinstance(obj, compass.Compass):
                # Get the pushbot vertex and ensure that the sensor is enabled
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.bot, new_objs, new_conns)

                ks = generic_robot_keyspace(i=1, f=1, d=2)
                pushbot_vertex.start_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(0, ks.key(),
                                                              9 << 27 | 100))
                c = nengo_spinnaker.utils.builder.IntermediateConnection(
                    mc_vertex, pushbot_vertex, keyspace=ks)
                new_conns.append(c)

                # Create a new compass calibration vertex and a connection from
                # the pushbot to it.
                cm = CompassVertex()
                new_objs.append(cm)
                new_conns.append(
                    nengo_spinnaker.utils.builder.IntermediateConnection(
                        pushbot_vertex, cm, keyspace=inbound_keyspace(i=1, s=9)
                    ))

                # Swap all outbound connections
                out_conns = [c for c in conns if c.pre is obj]

                for conn in out_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                        from_connection(conn)
                    c.pre = cm
                    new_conns.append(c)

            elif isinstance(obj, countspikes.CountSpikes):
                # Create the new CountSpikesVertex for the given region, add
                # connections from the retina to the CountSpikesVertex and
                # replace the origin on all relevant connections.
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.bot, new_objs, new_conns)

                csv = CountSpikesVertex(obj.region)
                new_objs.append(csv)

                # Add a new connection from the pushbot to the csv
                ks = inbound_keyspace(i=0, s=0, d=0)
                new_conns.append(
                    nengo_spinnaker.utils.builder.IntermediateConnection(
                        pushbot_vertex, csv, keyspace=ks))

                # Replace all connections out of the CountSpikesVertex
                out_conns = [c for c in conns if c.pre is obj]
                for c in out_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                        from_connection(c)
                    c.pre = csv
                    new_conns.append(c)

                # Add a new packet to the pushbot vertex to turn on the retina
                ks = generic_robot_keyspace(i=0, f=0, d=1)
                pushbot_vertex.start_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(0, ks.key(), 0))
                new_conns.append(
                    nengo_spinnaker.utils.builder.IntermediateConnection(
                        mc_vertex, pushbot_vertex, keyspace=ks))
            else:
                # Object is not a SpiNNaker->Robot or Robot->SpiNNaker
                new_objs.append(obj)

        # Add all remaining connections
        for c in conns:
            if not (isinstance(c.post, (motor.Motor, beep.Beep)) or
                    isinstance(c.pre, (accel.Accel, compass.Compass, gyro.Gyro,
                                       countspikes.CountSpikes))):
                new_conns.append(c)

        return new_objs, new_conns

    nengo_spinnaker.builder.Builder.register_connectivity_transform(
        prepare_pushbot)



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
            print transforms
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

    class CountSpikesVertex(nengo_spinnaker.utils.vertices.NengoVertex):
        MODEL_NAME = 'pushbot_countspikes'
        MAX_ATOMS = 1
        size_in = 0

        def __init__(self, region):
            super(CountSpikesVertex, self).__init__(1)
            """Create a new CountSpikesVertex for the given region."""
            self.region = region
            self.regions = []

        @classmethod
        def assemble(cls, csv, assembler):
            # Create the system region, the transforms region and the keys
            # region.
            system_region = nengo_spinnaker.utils.vertices.\
                UnpartitionedListRegion(list(csv.region))

            out_conns = nengo_spinnaker.utils.connections.Connections(
                assembler.get_outgoing_connections(csv))
            keys = list()
            for c in out_conns:
                for d in range(c.width):
                    keys.append(c.keyspace.key(d=d))
            keys.insert(0, len(keys))
            keys_region = nengo_spinnaker.utils.vertices.\
                UnpartitionedListRegion(keys)

            transforms = np.hstack(c.transform.reshape(c.transform.size) for c
                                   in out_conns).tolist()
            transforms = [nengo_spinnaker.utils.fp.bitsk(t) for t in
                          transforms]
            transforms.insert(0, len(transforms))
            transform_region = nengo_spinnaker.utils.vertices.\
                UnpartitionedListRegion(transforms)

            assert transforms[0] == keys[0]

            csv.regions = [system_region, transform_region, keys_region]
            return csv

    nengo_spinnaker.assembler.Assembler.register_object_builder(
        CountSpikesVertex.assemble, CountSpikesVertex)

except ImportError:
    pass
