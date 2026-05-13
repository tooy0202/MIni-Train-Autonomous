import rclpy
from rclpy.node import Node

from std_msgs.msg import String

import serial
import time


class ESP32SerialNode(Node):

    def __init__(self):
        super().__init__('esp32_serial_node')

        # serial
        self.ser = serial.Serial(
            '/dev/ttyUSB0',
            115200,
            timeout=1
        )

        time.sleep(2)

        # subscriber
        self.create_subscription(
            String,
            '/motor_command',
            self.motor_callback,
            10
        )

        self.get_logger().info(
            'ESP32 Serial Node Started'
        )

    def motor_callback(self, msg):

        cmd = msg.data

        self.ser.write(
            f'{cmd}\n'.encode()
        )

        self.get_logger().info(
            f'Sent to ESP32: {cmd}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = ESP32SerialNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()