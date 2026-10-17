from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('noise', default_value='0.5'),
        DeclareLaunchArgument('hysteresis', default_value='0.5'),
        Node(package='room_robot_pkg', executable='room_sim',
             parameters=[{'noise': LaunchConfiguration('noise')}]),
        Node(package='room_robot_pkg', executable='avoider',
             parameters=[{'hysteresis': LaunchConfiguration('hysteresis')}]),
    ])
