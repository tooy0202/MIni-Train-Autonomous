import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32, String
from geometry_msgs.msg import Twist


class ControlManagerNode(Node):
    def __init__(self):
        super().__init__('control_manager_node')

        self.mode = 'AUTO'
        self.target_speed = 0.5
        self.speed_limit = 1.0
        self.obstacle_status = 'NORMAL'

        self.create_subscription(
            Float32,
            '/speed_limit',
            self.speed_limit_callback,
            10
        )

        self.create_subscription(
            String,
            '/obstacle_status',
            self.obstacle_status_callback,
            10
        )

        self.cmd_pub = self.create_publisher(
            Twist,
            '/turtle1/cmd_vel',
            10
        )

        self.status_pub = self.create_publisher(
            String,
            '/train_status',
            10
        )

        self.timer = self.create_timer(0.1, self.control_loop)

        self.get_logger().info('Control Manager Node started')

    def speed_limit_callback(self, msg):
        self.speed_limit = msg.data

    def obstacle_status_callback(self, msg):
        self.obstacle_status = msg.data

    def control_loop(self):
        cmd = Twist()

        final_speed = min(self.target_speed, self.speed_limit)

        if self.obstacle_status == 'STOP':
            final_speed = 0.0

        cmd.linear.x = final_speed
        cmd.angular.z = 0.0

        self.cmd_pub.publish(cmd)

        status = String()
        status.data = (
            f'mode={self.mode}, '
            f'target_speed={self.target_speed:.2f}, '
            f'speed_limit={self.speed_limit:.2f}, '
            f'final_speed={final_speed:.2f}, '
            f'obstacle={self.obstacle_status}'
        )
        self.status_pub.publish(status)


def main(args=None):
    rclpy.init(args=args)
    node = ControlManagerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()