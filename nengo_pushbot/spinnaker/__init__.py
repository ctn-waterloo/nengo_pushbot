try:
    from nengo_spinnaker.builder import Builder

    from . import robot
    from .. import accel, beep, compass, gyro, motor

    # Create a connectivity transform to convert connections from
    # the Accelerometer into connections via a filter vertex.
    Builder.register_connectivity_transform(robot.SensorTransform(
        accel.Accel,
        robot.inbound_keyspace(i=1, s=8),  # Keyspace on pushbot->filter
        40.0,  # Transform the transforms on accel->obj connections
        [(robot.generic_robot_keyspace(i=1, f=1, d=2), 8 << 27 | 100)],  # on
        [(robot.generic_robot_keyspace(i=1, f=1, d=0), 0)],              # off
        filter_args={'size_in': 3}
    ))

    # Create a connectivity transform to convert connections from
    # the Gyro into connections via a filter vertex.
    Builder.register_connectivity_transform(robot.SensorTransform(
        gyro.Gyro,  # Replace objects of type gyro.Gyro
        robot.inbound_keyspace(i=1, s=7),  # Keyspace on pushbot->filter
        100.0,  # Transform the transforms on gyro->obj connections
        [(robot.generic_robot_keyspace(i=1, f=1, d=2), 7 << 27 | 100)],  # on
        [(robot.generic_robot_keyspace(i=1, f=1, d=0), 0)],              # off
        filter_args={'size_in': 3}
    ))

    # Create a connectivity transform to convert connections from the compass
    # into connections via a compass vertex
    from .compass import CompassVertex
    Builder.register_connectivity_transform(robot.SensorTransform(
        compass.Compass,
        robot.inbound_keyspace(i=1, s=9),
        1.0,
        [(robot.generic_robot_keyspace(i=1, f=1, d=2), 9 << 27 | 100)],  # on
        [(robot.generic_robot_keyspace(i=1, f=1, d=0), 0)],              # off
        filter_vertex_type=CompassVertex
    ))

    # Create a connectivity transform to convert connections to the beeper into
    # connections via a filter vertex.
    Builder.register_connectivity_transform(robot.ActuatorTransform(
        beep.Beep,
        robot.pwm_keyspace(i=36, p=0),  # Keyspace on filter->pushbot
        1000.0 / 2.0**15,  # Convert to mHz
        mc_to_pushbot_stop_keyspaces_payloads=[
            (robot.motor_keyspace(i=2, p=0, q=0, d=0), 0)  # Beeper off
        ],
        filter_args={'size_in': 2, 'transmission_period': 100}
    ))

    # Create a connectivity transform to convert connections to motors into
    # connections via a filter vertex.
    Builder.register_connectivity_transform(robot.ActuatorTransform(
        motor.Motor,
        robot.motor_keyspace(i=32, p=0, q=1),  # Keyspace on filter->pushbot
        100.0 / 2.0**15,  # Convert to +/- 100.0
        [(robot.motor_keyspace(i=2, p=0, q=0, d=0), 1)],  # Turn on the motors
        [(robot.motor_keyspace(i=2, p=0, q=0, d=0), 0)],  # Turn off the motors
        {'size_in': 2, 'transmission_period': 100}  # Arguments for the filter
    ))
except ImportError:
    pass
