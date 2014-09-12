from nengo_spinnaker.builder import Builder

from . import robot
from .. import accel, gyro, motor


# Create a connectivity transform to convert connections from
# the Accelerometer into connections via a filter vertex.
Builder.register_connectivity_transform(robot.sensor_transform(
    accel.Accel,
    robot.inbound_keyspace(i=1, s=8),  # Keyspace on pushbot->filter
    40.0,  # Transform the transforms on accel->obj connections
    [(robot.generic_robot_keyspace(i=1, f=1, d=2), 8 << 27 | 100)]  # Turn on
))

# Create a connectivity transform to convert connections from
# the Gyro into connections via a filter vertex.
Builder.register_connectivity_transform(robot.sensor_transform(
    gyro.Gyro,  # Replace objects of type gyro.Gyro
    robot.inbound_keyspace(i=1, s=7),  # Keyspace on pushbot->filter
    100.0,  # Transform the transforms on gyro->obj connections
    [(robot.generic_robot_keyspace(i=1, f=1, d=2), 7 << 27 | 100)],  # Turn on
    filter_args={'size_in': 3}
))

# Create a connectivity transform to convert connections to motors into
# connections via a filter vertex.
Builder.register_connectivity_transform(robot.actuator_transform(
    motor.Motor,
    robot.robot_keyspace(i=32, p=0, q=1),  # Keyspace on filter->pushbot
    100.0 / 2.0**15,  # Convert to +/- 100.0
    [(robot.motor_keyspace(i=2, p=0, q=0, d=0), 1)],  # Turn on the motors
    [(robot.motor_keyspace(i=2, p=0, q=0, d=0), 0)],  # Turn off the motors
    {'size_in': 2, 'transmission_period': 100}  # Arguments for the filter
))

# Create a connectivity transform to convert connections to the beeper into
# connections via a filter vertex.
Builder.register_connectivity_transform(robot.actuator_transform(
    beep.Beep,
    robot.pwm_keyspace(i=36, p=0),  # Keyspace on filter->pushbot
    100.0 / 2.0**15  # Transform the transforms on gyro->obj connections
    [(robot.motor_keyspace(i=2, p=0, q=0, d=0), 1)],  # Turn on the motors
    [(robot.motor_keyspace(i=2, p=0, q=0, d=0), 0)],  # Turn off the motors
    {'size_in': 2, 'transmission_period': 100}  # Arguments for the filter
))
