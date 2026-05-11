from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim'
        ),

        Node(
            package='lidar_avoidance',
            executable='avoidance',
            name='lidar_avoidance'
        ),

        Node(
            package='train_control',
            executable='control_manager',
            name='control_manager_node'
        ),
    ])