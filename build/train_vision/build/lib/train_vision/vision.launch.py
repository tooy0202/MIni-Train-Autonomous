from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        Node(
            package='train_vision',
            executable='camera',
            name='camera_node'
        ),

        Node(
            package='train_vision',
            executable='pose',
            name='pose_node'
        )

    ])