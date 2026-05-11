import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from cv_bridge import CvBridge

from ultralytics import YOLO

import cv2
from std_msgs.msg import String, Int32

import os
from datetime import datetime

import time

from train_vision.standing_detector import detect_standing

from train_vision.arm_detector import detect_arm_outside

class PoseNode(Node):

    def __init__(self):
        super().__init__('pose_node')

        self.bridge = CvBridge()

        self.model = YOLO('yolov8n-pose.pt')

        self.frame_count = 0
        self.skip_frames = 3

        self.last_person_count = -1

        self.save_count = 0

        self.standing_start_time = None
        self.standing_image_saved = False
        self.standing_alert_sent = False
        self.standing_confirm_time = 3.0
        self.hand_outside_start_time = None
        self.hand_image_saved = False
        self.hand_alert_sent = False
        self.hand_confirm_time = 3.0

        self.hip_standing_line = 260

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

        # skip frame
        if self.frame_count % self.skip_frames != 0:
            return

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        # resize image
        frame = cv2.resize(frame, (640, 384))

        # inference
        results = self.model(
            frame,
            imgsz=384,
            conf=0.65,
            device=0,
            verbose=False
        )

        person_count = 0

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                # COCO class 0 = person
                if cls_id == 0 and conf >= 0.65:
                    person_count += 1
#แจ้งเตือนถ้าคนยืนเกิน 3 วิ---------------------------------
#ยืน
        is_standing = False

        for result in results:
            if detect_standing(self, result):
                is_standing = True
                break

        alert = 'NORMAL'

        if is_standing:
            if self.standing_start_time is None:
                self.standing_start_time = time.time()
                self.standing_image_saved = False

            standing_duration = time.time() - self.standing_start_time

            if standing_duration >= self.standing_confirm_time:
                alert = 'STANDING'
        else:
            self.standing_start_time = None
            self.standing_image_saved = False

        if len(results) > 0:
            annotated_frame = results[0].plot()

            SAFE_LEFT = 120
            SAFE_RIGHT = 520

            cv2.line(
                annotated_frame,
                (SAFE_LEFT, 0),
                (SAFE_LEFT, 384),
                (0, 255, 255),
                2
            )

            cv2.line(
                annotated_frame,
                (SAFE_RIGHT, 0),
                (SAFE_RIGHT, 384),
                (0, 255, 255),
                2
            )

        else:
            annotated_frame = frame

        if alert == 'STANDING' and not self.standing_image_saved:

            self.save_count += 1

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            filename = (
                f'{self.save_count}_STANDING_ALERT_persons_{person_count}_{timestamp}.jpg'
            )

            filepath = os.path.join(self.save_dir, filename)

            cv2.imwrite(filepath, annotated_frame)

            self.get_logger().info(
                f'STANDING ALERT saved: {filepath} | persons={person_count}'
            )

            self.standing_image_saved = True
#-----------------------------------------------
        is_arm_outside = False

        for result in results:
            if detect_arm_outside(self, result):
                is_arm_outside = True
                break
        
        alert_hand = 'NORMAL'

        if is_arm_outside:
            if self.hand_outside_start_time is None:
                self.hand_outside_start_time = time.time()
                self.hand_image_saved = False

            hand_duration = time.time() - self.hand_outside_start_time

            if hand_duration >= self.hand_confirm_time:
                alert_hand = 'ARM_OUTSIDE'
        else:
            self.hand_outside_start_time = None
            self.hand_image_saved = False

        final_alert = 'NORMAL'
        
        if alert == 'STANDING':
            final_alert = 'WARNING_STANDING'

        if alert_hand == 'ARM_OUTSIDE':
            final_alert = 'DANGER_ARM_OUTSIDE'
        
        if alert == 'STANDING' and alert_hand != 'ARM_OUTSIDE':
            final_alert = 'DANGER!!!'

        HIP_STANDING_LINE = self.hip_standing_line

        cv2.line(
            annotated_frame,
            (0, HIP_STANDING_LINE),
            (640, HIP_STANDING_LINE),
            (255, 0, 0),
            2
        )

        cv2.putText(
            annotated_frame,
            f'FINAL ALERT: {final_alert}',
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.putText(
            annotated_frame,
            f'Persons: {person_count}',
            (20, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        self.alert_pub.publish(String(data=final_alert))
        self.person_count_pub.publish(Int32(data=person_count))

        standing_time_text = 0.0
        hand_time_text = 0.0

        if is_standing:
            standing_time_text = standing_duration

        if is_arm_outside:
            hand_time_text = hand_duration

        self.get_logger().info(
            f'FINAL_ALERT={final_alert} | '
            f'persons={person_count} | '
            f'standing_time={standing_time_text:.1f}s | '
            f'hand_time={hand_time_text:.1f}s',
            throttle_duration_sec=1.0
        )

        if alert_hand == 'ARM_OUTSIDE' and not self.hand_image_saved:

            self.save_count += 1

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            filename = (
                f'{self.save_count}_HAND_OUTSIDE_ALERT_persons_{person_count}_{timestamp}.jpg'
            )

            filepath = os.path.join(self.save_dir, filename)

            cv2.imwrite(filepath, annotated_frame)

            self.get_logger().info(
                f'HAND_OUTSIDE_ALERT saved: {filepath} | persons={person_count}'
            )

            self.hand_image_saved = True

def main(args=None):
    rclpy.init(args=args)

    node = PoseNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()