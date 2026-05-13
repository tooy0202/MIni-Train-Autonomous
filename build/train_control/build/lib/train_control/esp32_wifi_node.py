import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import socket


class ESP32WiFiNode(Node):

    def __init__(self):
        super().__init__('esp32_wifi_node')

        self.esp32_ip = '172.20.10.7'
        self.port = 8888

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.esp32_ip, self.port))

        self.create_subscription(
            String,
            '/motor_command',
            self.motor_callback,
            10
        )

        self.get_logger().info('ESP32 WiFi Node Started')

    def motor_callback(self, msg):
        cmd = msg.data
        self.sock.sendall(f'{cmd}\n'.encode())

        self.get_logger().info(f'Sent to ESP32: {cmd}')


def main(args=None):
    rclpy.init(args=args)
    node = ESP32WiFiNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()