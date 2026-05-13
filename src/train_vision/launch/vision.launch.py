from launch import LaunchDescription
from launch.actions import TimerAction
from launch_ros.actions import Node


def generate_launch_description():

    camera_front = Node(
        package='train_vision',
        executable='camera',
        name='camera_front',
        parameters=[{
            'camera_id': 0,
            'topic_name': '/camera/front/image_raw'
        }]
    )

    camera_back = Node(
        package='train_vision',
        executable='camera',
        name='camera_back',
        parameters=[{
            'camera_id': 2,
            'topic_name': '/camera/back/image_raw'
        }]
    )

    pose_manager = Node(
        package='train_vision',
        executable='pose_manager',
        name='pose_manager_node'
    )

    return LaunchDescription([
        camera_front,
        camera_back,
        TimerAction(period=5.0, actions=[pose_manager]),
    ])