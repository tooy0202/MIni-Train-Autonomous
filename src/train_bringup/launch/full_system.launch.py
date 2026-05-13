from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

import os


def generate_launch_description():

    livox_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('lidar_avoidance'),
                'launch',
                'livox_only.launch.py'
            )
        )
    )

    lidar_avoidance = Node(
        package='lidar_avoidance',
        executable='avoidance',
        name='lidar_avoidance'
    )

    control_manager = Node(
        package='train_control',
        executable='control_manager',
        name='control_manager_node'
    )

    esp32_wifi = Node(
        package='train_control',
        executable='esp32_wifi',
        name='esp32_wifi_node'
    )

    vision_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                os.getenv('HOME'),
                'ws_1/src/train_vision/launch/vision.launch.py'
            )
        )
    )

    return LaunchDescription([
        livox_launch,
        lidar_avoidance,
        control_manager,
        esp32_wifi,
        vision_launch
    ])