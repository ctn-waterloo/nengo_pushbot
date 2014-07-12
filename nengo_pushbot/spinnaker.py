import numpy as np

from . import accel, beep, compass, gyro, motor, tracker

try:
    import nengo_spinnaker

    import nengo_spinnaker.builder
    import pacman103.front.common

    generic_robot_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundRobotProtocol', [('x', 1), ('o', 19), ('c', 1), ('i', 7),
                                  ('f', 1), ('d', 3)], 'xoi', 'xoi')(
        x=1, o=2**19-1)

    motor_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundMotorProtocol',
        [('x', 1), ('_', 19), ('c', 1), ('i', 7), ('f', 1), ('p', 1), ('q', 1),
         ('d', 1)], 'x_i', 'x_i')(x=1, _=2**19-1, f=0)

    pwm_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundPwmProtocol', [('x', 1), ('o', 19), ('c', 1), ('i', 7),
                                ('f', 1), ('p', 2), ('d', 1)],
        'xoi', 'xoi')(x=1, o=2**19-1, f=0)

    # o for object (0xFEFFF8), i for ID (of UART), s for sensor, d for
    # dimension
    inbound_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'InboundRobotKeyspace', [('o', 21), ('i', 4), ('s', 5), ('d', 2)],
        'ois', 'ois')(o=0xFEFFF8 >> 3)

    retina_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'InboundRetinaKeyspace', [('o', 17), ('i', 15)], 'o', 'o')

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

            elif isinstance(obj, tracker.Tracker):
                # Get the pushbot vertex and ensure that the sensor is enabled
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.bot, new_objs, new_conns)

                # Turn on the retina
                pushbot_vertex.start_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(
                        0,
                        generic_robot_keyspace(d=1).key(),
                        2 << 29 | 1 << 26
                    )
                )

                # Set the retina key
                pushbot_vertex.start_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(
                        0,
                        generic_robot_keyspace(d=2).key(),
                        0xFAFB << 16
                    )
                )

                # Create a new TrackerVertex and add a connection from the
                # eDVS to the TrackerVertex.
                tracker_vertex = TrackerVertex(obj.frequency)
                new_objs.append(tracker_vertex)

                # Add a new connection from the pushbot vertex to the tracker
                # vertex
                new_conns.append(
                    nengo_spinnaker.utils.builder.IntermediateConnection(
                        pushbot_vertex, tracker_vertex,
                        keyspace=retina_keyspace(o=0xFAFB)))

                # Replace all connections coming from the TrackerVertex
                out_conns = [c for c in conns if c.pre is obj]
                for c in out_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                        from_connection(c)
                    c.pre = tracker_vertex
                    new_conns.append(c)
            else:
                # Object is not a SpiNNaker->Robot or Robot->SpiNNaker
                new_objs.append(obj)

        # Add all remaining connections
        for c in conns:
            if not (isinstance(c.post, (motor.Motor, beep.Beep)) or
                    isinstance(c.pre, (accel.Accel, compass.Compass, gyro.Gyro,
                                       tracker.Tracker))):
                new_conns.append(c)

        return new_objs, new_conns

    nengo_spinnaker.builder.Builder.register_connectivity_transform(
        prepare_pushbot)

    def get_vertex(bot, objects, connections):
        """Return the vertex for the robot, and an amended set of objects and
        connections.
        """
        objects = list(objects)
        connections = list(connections)

        edge_dirs = {'EAST': 0, 'NORTH EAST': 1, 'NORTH': 2, 'WEST': 3,
                     'SOUTH WEST': 4, 'SOUTH': 5}

        if not hasattr(bot, 'external_vertex'):
            # Create the external vertex
            setattr(bot, 'external_vertex', PushBotVertex(
                connected_node_coords=dict(
                    x=bot.spinnaker_address[0],
                    y=bot.spinnaker_address[1]),
                connected_node_edge=edge_dirs[bot.spinnaker_address[2]]))
            objects.append(bot.external_vertex)

            # Create a link between the multicast vertex and the pushbot
            # vertex to turn various components on
            setattr(bot, 'mc_vertex',
                    nengo_spinnaker.assembler.MulticastPlayer())
            objects.append(bot.mc_vertex)

            # Set the LED or Laser frequencies
            if bot.led_freq is not None and bot.led_freq > 0:
                ks = pwm_keyspace(i=37, p=0, d=0)
                bot.external_vertex.start_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(
                        0, ks.key(), bot.led_freq * 1000.))
                bot.external_vertex.end_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(0, ks.key(), 0))

                connections.append(
                    nengo_spinnaker.utils.builder.IntermediateConnection(
                        bot.mc_vertex, bot.external_vertex, keyspace=ks))

            if bot.laser_freq is not None and bot.laser_freq > 0:
                ks = pwm_keyspace(i=37, p=0, d=1)
                bot.external_vertex.start_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(
                        0, ks.key(), bot.laser_freq * 1000.))
                bot.external_vertex.end_packets.append(
                    nengo_spinnaker.assembler.MulticastPacket(0, ks.key(), 0))

                connections.append(
                    nengo_spinnaker.utils.builder.IntermediateConnection(
                        bot.mc_vertex, bot.external_vertex, keyspace=ks))

        # Return a reference to the external vertex, the objects and the
        # connections
        return bot.external_vertex, bot.mc_vertex, objects, connections

    class PushBotVertex(pacman103.front.common.ExternalDeviceVertex):
        model_name = "nengo_pushbot"
        size_in = 2

        def __init__(self,
                     virtual_chip_coords=dict(x=0xFE, y=0xFF),
                     connected_node_coords=dict(x=1, y=0),
                     connected_node_edge=pacman103.front.common.edges.EAST,
                     index=0):
            super(PushBotVertex, self).__init__(
                n_neurons=0, virtual_chip_coords=virtual_chip_coords,
                connected_node_coords=connected_node_coords,
                connected_node_edge=connected_node_edge
            )
            self.start_packets = [nengo_spinnaker.assembler.MulticastPacket(
                0, generic_robot_keyspace(i=0, f=0, d=7).key(), 0)
            ]
            self.end_packets = [nengo_spinnaker.assembler.MulticastPacket(
                0, generic_robot_keyspace(i=1, f=0, d=0).key(), 0)
            ]
            self.index = index

        def generate_routing_info(self, subedge):
            return (subedge.edge.keyspace.routing_key(),
                    subedge.edge.keyspace.routing_mask)

    class SensorVertex(nengo_spinnaker.utils.vertices.NengoVertex):
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

    class CompassVertex(SensorVertex):
        """Application to provide calibrated compass data."""
        MODEL_NAME = 'pushbot_compass_calibrate'
        MAX_ATOMS = 1
        size_in = 3

        def __init__(self):
            super(CompassVertex, self).__init__(1)
            self.regions = [None, None, None]

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

    class TrackerVertex(SensorVertex):
        MODEL_NAME = 'pushbot_tracker'
        MAX_ATOMS = 1
        size_in = 0
        size_out = 3

        def __init__(self, frequency, sigma_t=100, sigma_p=30, eta=0.3):
            super(TrackerVertex, self).__init__(1)
            # Create space for the regions
            self.regions = [None] * 5

            # Create the system region
            t_exp = (1./frequency) * 10.0**6  # The expected delta t in usecs
            system_items = [
                nengo_spinnaker.utils.fp.bitsk(eta, n_bits=16, n_frac=16,
                                               signed=False),
                t_exp]

            self.regions[0] = nengo_spinnaker.utils.vertices.\
                UnpartitionedListRegion(system_items)

            # Construct the Gaussians for time and space
            t = np.arange(10*sigma_t).astype(float)
            gaussian_time = nengo_spinnaker.utils.fp.bitsk(
                np.exp(-t**2 / (2*sigma_t**2)), n_bits=16, n_frac=16,
                signed=False)
            gaussian_time.insert(0, len(gaussian_time))
            gtr = nengo_spinnaker.utils.vertices.UnpartitionedListRegion(
                gaussian_time, dtype='uint16')

            s = np.arange(256).astype(float)
            gaussian_space = nengo_spinnaker.utils.fp.bitsk(
                np.exp(-s**2 / (2*sigma_p**2)), n_bits=16, n_frac=16,
                signed=False)
            gsr = nengo_spinnaker.utils.vertices.UnpartitionedListRegion(
                gaussian_space, dtype='uint16')

            # Assign the Gaussian region
            self.regions[3] = gsr
            self.regions[4] = gtr

        @classmethod
        def assemble(cls, tracker, assembler):
            # Get the output keys and transform for the vertex
            keys_region = cls.get_output_keys_region(tracker, assembler)
            keys_region.data.insert(0, len(keys_region.data))
            _, transform_region = cls.get_transform(tracker, assembler)
            keys_region.size += 1

            tracker.regions[1] = keys_region
            tracker.regions[2] = transform_region

            return tracker

    nengo_spinnaker.assembler.Assembler.register_object_builder(
        TrackerVertex.assemble, TrackerVertex)

except ImportError:
    pass
