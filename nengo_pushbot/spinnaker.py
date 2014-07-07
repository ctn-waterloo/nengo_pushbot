import nengo
from . import motor

try:
    import nengo_spinnaker

    import nengo_spinnaker.builder
    import pacman103.front.common

    generic_robot_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundRobotProtocol', [('x', 1), ('_', 20), ('i', 7), ('__', 4)],
        'x_i')(x=1, _=2**20-1)

    motor_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'OutboundMotorProtocol',
        [('x', 1), ('_', 20), ('i', 7), ('f', 1), ('p', 1), ('q', 1),
         ('d', 1)], 'x_i')(x=1, _=2**20-1, f=1)

    inbound_keyspace = nengo_spinnaker.utils.keyspaces.create_keyspace(
        'InboundRobotKeyspace', [('o', 21), ('i', 9), ('d', 2)], 'oi')

    def prepare_pushbot(objs, conns, probes):
        # TODO
        #  - Compass/gyro
        #  - LED
        #  - Laser
        #  - Beeper
        #  - eDVS
        new_objs = list()
        new_conns = list()

        # Investigate the objects
        for obj in objs:
            if not isinstance(obj, motor.Motor):
                # Object is not a Tracks, so we just retain it
                new_objs.append(obj)
                continue

            # Create a filter vertex between all incoming edges and the tracks
            # vertex.
            fv = nengo_spinnaker.builder.IntermediateFilter(obj.size_in)
            new_objs.append(fv)

            in_conns = [c for c in conns if c.post == obj]
            for c in in_conns:
                c = nengo_spinnaker.utils.builder.IntermediateConnection.\
                    from_connection(c)
                c.post = fv
                c.transform *= 100. / 2.**15
                new_conns.append(c)

            # Get the robot vertex
            pushbot_vertex, mc_vertex, new_objs, new_conns =\
                get_vertex(obj.robot, new_objs, new_conns)

            # Add the motor enable/disable commands to the pushbot vertex
            pushbot_vertex.start_packets.append(
                nengo_spinnaker.assembler.MulticastPacket(
                    0, motor_keyspace(i=2, p=0, q=0, d=0).key(), 1))
            pushbot_vertex.end_packets.append(
                nengo_spinnaker.assembler.MulticastPacket(
                    0, motor_keyspace(i=2, p=0, q=0, d=0).key(), 0))

            # Create a new connection from the multicast vertex to the pushbot
            # vertex
            new_conns.append(
                nengo_spinnaker.utils.builder.IntermediateConnection(
                    mc_vertex, pushbot_vertex,
                    keyspace=motor_keyspace(i=2, p=0, q=0, d=0)))

            # Create a new connection between the filter vertex and the pushbot
            c = nengo_spinnaker.utils.builder.IntermediateConnection(
                fv, pushbot_vertex, keyspace=motor_keyspace(i=32, p=0, q=1))
            new_conns.append(c)

        # Add all remaining connections
        for c in conns:
            if isinstance(c.post, motor.Motor):
                continue
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
                     connected_node_edge=pacman103.front.common.edges.EAST):
            super(PushBotVertex, self).__init__(
                n_neurons=0, virtual_chip_coords=virtual_chip_coords,
                connected_node_coords=connected_node_coords,
                connected_node_edge=connected_node_edge
            )
            self.start_packets = list()
            self.end_packets = list()

        def generate_routing_info(self, subedge):
            return (subedge.edge.keyspace.routing_key(),
                    subedge.edge.keyspace.routing_mask)
                    
except ImportError:
    pass