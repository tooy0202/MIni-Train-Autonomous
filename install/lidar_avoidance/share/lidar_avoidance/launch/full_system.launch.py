from launch import LaunchDescription
from launch_ros.actions import Node
import os

def generate_launch_description():

    config_path = os.path.join(
        os.getenv('HOME'),
        'ws_1/src/livox_ros_driver2/config/MID360_config.json'
    )

    return LaunchDescription([

        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim'
        ),

        Node(
            package='livox_ros_driver2',
            executable='livox_ros_driver2_node',
            name='livox_lidar_publisher',
            parameters=[{
                'user_config_path': config_path
            }]
        ),

        Node(
            package='lidar_avoidance',
            executable='avoidance',
            name='avoidance'
        )
    ])