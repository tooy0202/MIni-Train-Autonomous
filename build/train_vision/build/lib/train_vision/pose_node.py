import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from ultralytics import YOLO

import cv2
from std_msgs.msg import String, Int32

import torch

import os

from train_vision.standing_detector import detect_standing

from train_vision.arm_detector import detect_arm_outside

from train_vision.overlay_drawer import draw_overlay

from train_vision.image_logger import save_alert_image

from train_vision.alert_manager import update_alert_state


class PoseNode(Node):

    def __init__(self):
        super().__init__('pose_node')

        self.bridge = CvBridge()

        self.model = YOLO('/home/jetson/ws_1/yolov8n-pose.pt')
        self.model.fuse = lambda *args, **kwargs: self.model

        self.frame_count = 0
        self.skip_frames = 3
        self.save_count = 0
        # STANDING
        self.standing_start_time = None
        self.standing_image_saved = False
        self.standing_confirm_time = 3.0
        # ARM OUTSIDE
        self.hand_outside_start_time = None
        self.hand_image_saved = False
        self.hand_confirm_time = 3.0
        # ระยะที่กำหนด แอว, ซ้าย, ขวา
        self.hip_standing_line = 260
        self.safe_left = 120
        self.safe_right = 520

        self.alert_pub = self.create_publisher(
            String,
            '/passenger_alert',
            10
        )

        self.person_count_pub = self.create_publisher(
            Int32,
            '/passenger_count',
            10
        )

        self.save_dir = os.path.join(
            os.path.expanduser('~'),
            'person_logs'
        )

        os.makedirs(self.save_dir, exist_ok=True)

        self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10
        )

        self.get_logger().info('Pose Node Started')


    def image_callback(self, msg):

        self.frame_count += 1

        if self.frame_count % self.skip_frames != 0:
            return

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        frame = cv2.resize(frame, (640, 384))

        torch.cuda.empty_cache()

        results = self.model(
            frame,
            imgsz=384,
            conf=0.65,
            device=0,
            verbose=False
        )

        # 1) count persons
        person_count = 0

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                if cls_id == 0 and conf >= 0.65:
                    person_count += 1

        # 2) detect standing
        is_standing = False

        for result in results:
            if detect_standing(self, result):
                is_standing = True
                break

        # 3) detect arm outside
        is_arm_outside = False

        for result in results:
            if detect_arm_outside(self, result):
                is_arm_outside = True
                break

        # 4) update alert state
        final_alert, alert, alert_hand, standing_duration, hand_duration = update_alert_state(
            self,
            is_standing,
            is_arm_outside
        )

        # 5) draw pose result
        if len(results) > 0:
            annotated_frame = results[0].plot()
        else:
            annotated_frame = frame

        # 6) draw overlay
        annotated_frame = draw_overlay(
            annotated_frame,
            final_alert,
            person_count,
            self.safe_left,
            self.safe_right,
            self.hip_standing_line
        )

        # 7) save standing image
        if alert == 'STANDING' and not self.standing_image_saved:

            self.save_count += 1

            filepath = save_alert_image(
                self.save_dir,
                self.save_count,
                'STANDING_ALERT',
                person_count,
                annotated_frame
            )

            self.get_logger().info(
                f'STANDING_ALERT saved: {filepath} | persons={person_count}'
            )

            self.standing_image_saved = True

        # 8) save arm outside image
        if alert_hand == 'ARM_OUTSIDE' and not self.hand_image_saved:

            self.save_count += 1

            filepath = save_alert_image(
                self.save_dir,
                self.save_count,
                'HAND_OUTSIDE_ALERT',
                person_count,
                annotated_frame
            )

            self.get_logger().info(
                f'HAND_OUTSIDE_ALERT saved: {filepath} | persons={person_count}'
            )

            self.hand_image_saved = True

        # 9) publish
        self.alert_pub.publish(String(data=final_alert))
        self.person_count_pub.publish(Int32(data=person_count))

        # 10) log
        self.get_logger().info(
            f'FINAL_ALERT={final_alert} | '
            f'persons={person_count} | '
            f'standing_time={standing_duration:.1f}s | '
            f'hand_time={hand_duration:.1f}s',
            throttle_duration_sec=1.0
        )

def main(args=None):
    rclpy.init(args=args)

    node = PoseNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()