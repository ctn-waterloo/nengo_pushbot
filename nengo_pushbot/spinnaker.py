from . import accel, beep, compass, gyro, motor

try:
    import nengo_spinnaker

    import nengo_spinnaker.builder
    import pacman103.front.common

    generic_robot_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundRobotProtocol', [('x', 1), ('o', 20), ('i', 7), ('f', 1),
                                  ('d', 3)], 'xoi')(x=1, o=2**20-1)

    motor_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundMotorProtocol',
        [('x', 1), ('_', 20), ('i', 7), ('f', 1), ('p', 1), ('q', 1),
         ('d', 1)], 'x_i')(x=1, _=2**20-1, f=0)

    pwm_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundPwmProtocol', [('x', 1), ('o', 20), ('i', 7), ('f', 1),
                                ('p', 2), ('d', 1)],
        'xoi')(x=1, o=2**20-1, f=0)

    # o for object (0xFEFFF8), i for ID (of UART), s for sensor, d for
    # dimension
    inbound_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'InboundRobotKeyspace', [('o', 21), ('i', 4), ('s', 5), ('d', 2)],
        'ois')(o=0xFEFFF8 >> 3)

    def prepare_pushbot(objs, conns, probes):
        new_objs = list()
        new_conns = list()

        # Investigate the objects
        for obj in objs:
            if not isinstance(obj, (motor.Motor, beep.Beep)):
                # Create a filter vertex between all incoming edges and the
                # object
                fv = nengo_spinnaker.builder.IntermediateFilter(obj.size_in)
                new_objs.append(fv)

                in_conns = [c for c in conns if c.post is obj]
                for c in in_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                        from_connection(c)
                    c.post = fv
                    if isinstance(obj, motor.Motor):
                        c.transform *= 100. / 2.**15  # Value to range +/- 100
                    elif isinstance(obj, beep.Beep):
                        c.transform *= 1000. / 2.**15  # Value to mHz
                    new_conns.append(c)

                # Get the robot vertex
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.robot, new_objs, new_conns)

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

                # Create a new connection between the filter vertex and the
                # pushbot
                if isinstance(obj, motor.Motor):
                    c = nengo_spinnaker.utils.builder.IntermediateConnection(
                        fv, pushbot_vertex,
                        keyspace=motor_keyspace(i=32, p=0, q=1))
                elif isinstance(obj, beep.Beep):
                    c = nengo_spinnaker.utils.builder.IntermediateConnection(
                        fv, pushbot_vertex, keyspace=pwm_keyspace())
                new_conns.append(c)

            elif isinstance(obj, (accel.Accel, compass.Compass, gyro.Gyro)):
                # Ensure the appropriate sensor is activated, then provide the
                # appropriate edge from the pushbot vertex to the targets of
                # the objects
                pushbot_vertex, mc_vertex, new_objs, new_conns =\
                    get_vertex(obj.robot, new_objs, new_conns)

                # Add commands to enable appropriate sensors
                ks = generic_robot_keyspace(i=1, f=1, d=1)
                if isinstance(accel.Accel):
                    pushbot_vertex.append(
                        nengo_spinnaker.assembler.MulticastPacket(0, ks,
                                                                  8 << 27 | 10)
                    )
                elif isinstance(compass.Compass):
                    pushbot_vertex.append(
                        nengo_spinnaker.assembler.MulticastPacket(0, ks,
                                                                  9 << 27 | 10)
                    )
                elif isinstance(gyro.Gyro):
                    pushbot_vertex.append(
                        nengo_spinnaker.assembler.MulticastPacket(0, ks,
                                                                  7 << 27 | 10)
                    )

                # Modify connections from this object to have their pre as the
                # pushbot vertex and their keys as the appropriate form
                out_conns = [c for c in conns if c.pre is obj]

                for conn in out_conns:
                    c = nengo_spinnaker.utils.builder.IntermediateConnections.\
                        from_connection(conn)
                    fv = nengo_spinnaker.builder.IntermediateFilter(
                        c.pre.size_out)
                    if isinstance(obj, accel.Accel):
                        c.keyspace = inbound_keyspace(i=1, s=8)
                        c.transform *= 10000.
                    elif isinstance(obj, compass.Compass):
                        c.keyspace = inbound_keyspace(i=1, s=9)
                    elif isinstance(obj, gyro.Gyro):
                        c.keyspace = inbound_keyspace(i=1, s=7)
                        c.transform *= 5000.
            else:
                # Object is not a SpiNNaker->Robot or Robot->SpiNNaker
                new_objs.append(obj)

        # Add all remaining connections
        for c in conns:
            if not (isinstance(c.post, (motor.Motor, beep.Beep)) or
                    isinstance(c.pre, (accel.Accel, compass.Compass, gyro.Gyro)
                               )):
                new_conns.append(c)

        return new_objs, new_conns

    nengo_spinnaker.builder.Builder.register_connectivity_transform(
        prepare_pushbot)

    def get_vertex(self, objects, connections):
        """Return the vertex for the robot, and an amended set of objects and
        connections.
        """
        objects = list(objects)
        connections = list(connections)

        if self.external_vertex is None:
            # Create the external vertex
            self.external_vertex = PushBotVertex()
            objects.append(self.external_vertex)

            # Create a link between the multicast vertex and the pushbot
            # vertex to turn various components on
            self.mc_vertex = nengo_spinnaker.assembler.MulticastPlayer()
            objects.append(self.mc_vertex)

        # Return a reference to the external vertex, the objects and the
        # connections
        return self.external_vertex, self.mc_vertex, objects, connections

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
            self.start_packets = list()
            self.end_packets = list()
            self.index = index

        def generate_routing_info(self, subedge):
            return (subedge.edge.keyspace.routing_key(),
                    subedge.edge.keyspace.routing_mask)

except ImportError:
    pass
