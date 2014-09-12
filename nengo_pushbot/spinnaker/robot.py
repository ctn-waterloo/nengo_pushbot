import numpy as np

import nengo_spinnaker
from nengo_spinnaker.assembler import MulticastPacket
from nengo_spinnaker import connection
from nengo_spinnaker import node
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

# Directions mapped to link indices
edge_dirs = {'EAST': 0, 'E': 0,
             'NORTH EAST': 1, 'NE': 1, 'NORTHEAST': 1, 'NORTH-EAST': 1,
             'NORTH': 2, 'N': 2,
             'WEST': 3, 'W': 3,
             'SOUTH WEST': 4, 'SW': 4, 'SOUTHWEST': 4, 'SOUTH-WEST': 4,
             'SOUTH': 5, 'S': 5}


def sensor_transform(sensor_type, pushbot_to_filter_keyspace,
                     filter_out_transform=1.,
                     mc_to_pushbot_start_keyspaces_payloads=list(),
                     mc_to_pushbot_stop_keyspaces_payloads=list(),
                     filter_args=dict()):
    """Create a new function to transform sensors and their outgoing
    connections into filter vertices and associated connections.

    :param sensor_type: Class of sensor to modify
    :param pushbot_to_filter_keyspace: The keyspace with which to expect
                                       packets from the pushbot vertex.
    :param filter_out_modifier: Function to modify functions from the filter
                                vertex.
    """
    def prepare_sensor(objs, conns, probes):
        """Replace sensor objects with connections from the pushbot vertex and
        ensure that the sensor feedback is enabled.
        """
        # Create a list of objects and connections which are nothing to do with
        # accelerometers
        new_objs = [o for o in objs if not isinstance(o, sensor_type)]
        new_conns = [c for c in conns if
                     not isinstance(c.pre_obj, sensor_type) and
                     not isinstance(c.post_obj, sensor_type)]

        # Replace all accelerometer objects with the pushbot vertex, modify all
        # connections from the accelerometer.
        sensors = [o for o in objs if isinstance(o, sensor_type)]
        for obj in sensors:
            # Get the pushbot vertex and multicast vertex
            pushbot_vertex, mc_vertex, os, cs = get_vertex(obj.bot)
            new_objs.extend(os)
            new_conns.extend(cs)

            # Create a new filter vertex, with incoming connection from the
            # pushbot vertex
            fv = node.IntermediateFilter(**filter_args)
            new_objs.append(fv)
            new_conns.append(connection.IntermediateConnection(
                pushbot_vertex, fv, keyspace=pushbot_to_filter_keyspace))

            # Modify all the connections from the accelerometer to have
            # them start at the filter vertex.
            in_conns = [c for c in conns if c.pre_obj is obj]
            for c in in_conns:
                c = connection.IntermediateConnection.from_connection(c)
                c.pre_obj = fv
                c.transform = np.dot(filter_out_transform, c.transform)
                new_conns.append(c)

            # Add new packets to the pushbot vertex to ensure that
            # sensor data is switched on and off.
            for (ks, payload) in mc_to_pushbot_start_keyspaces_payloads:
                pushbot_vertex.start_packets.append(
                    MulticastPacket(0, ks.key(), payload))
                new_conns.append(connection.IntermediateConnection(
                    mc_vertex, pushbot_vertex, keyspace=ks))

            for (ks, payload) in mc_to_pushbot_stop_keyspaces_payloads:
                pushbot_vertex.end_packets.append(
                    MulticastPacket(0, ks.key(), payload))
                new_conns.append(connection.IntermediateConnection(
                    mc_vertex, pushbot_vertex, keyspace=ks))

        # Return the new objects and new connections list
        return new_objs, new_conns

    return prepare_sensor


def get_vertex(bot):
    """Return the vertex for the robot, and an amended set of objects and
    connections.
    """
    objects = list()
    connections = list()

    if not hasattr(bot, 'external_vertex'):
        # Create the external vertex
        setattr(bot, 'external_vertex', PushBotVertex(
            connected_node_coords=dict(x=bot.spinnaker_address[0],
                                       y=bot.spinnaker_address[1]),
            connected_node_edge=edge_dirs[bot.spinnaker_address[2]]))
        objects.append(bot.external_vertex)

        # Create a link between the multicast vertex and the pushbot vertex to
        # turn various components on
        setattr(bot, 'mc_vertex', nengo_spinnaker.assembler.MulticastPlayer())
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
    """PACMAN vertex representing a PushBot connected to SpiNNlink.
    """
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
