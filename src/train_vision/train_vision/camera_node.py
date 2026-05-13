import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

import cv2


class CameraNode(Node):

    def __init__(self):
        super().__init__('camera_node')

        self.declare_parameter('camera_id', 0)
        self.declare_parameter('topic_name', '/camera/image_raw')

        camera_id = self.get_parameter('camera_id').value
        topic_name = self.get_parameter('topic_name').value

        self.cap = cv2.VideoCapture(camera_id)
        self.bridge = CvBridge()

        self.image_pub = self.create_publisher(
            Image,
            topic_name,
            10
        )

        self.timer = self.create_timer(0.1, self.publish_frame)

        self.get_logger().info(
            f'Camera Node started | camera_id={camera_id} | topic={topic_name}'
        )

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