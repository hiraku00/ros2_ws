from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(package='room_robot_pkg', executable='room_sim', parameters=[{'noise': 0.5}]),
        Node(package='room_robot_pkg', executable='avoider', parameters=[{'hysteresis': 0.5}]),
    ])
