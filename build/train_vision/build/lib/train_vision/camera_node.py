import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2


class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')

        self.cap = cv2.VideoCapture(0)
        self.bridge = CvBridge()

        self.image_pub = self.create_publisher(
            Image,
            '/camera/image_raw',
            10
        )

        self.timer = self.create_timer(0.1, self.publish_frame)

        self.get_logger().info('Camera Node started')

    def publish_frame(self):
        ret, frame = self.cap.read()

        if not ret:
            self.get_logger().warn('Cannot read frame from camera')
            return

        msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')
        self.image_pub.publish(msg)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()