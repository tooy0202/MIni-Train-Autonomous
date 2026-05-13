import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image
from std_msgs.msg import String, Int32
from cv_bridge import CvBridge

from ultralytics import YOLO

import cv2
import torch
import os

from train_vision.standing_detector import detect_standing
from train_vision.arm_detector import detect_arm_outside
from train_vision.overlay_drawer import draw_overlay
from train_vision.image_logger import save_alert_image
from train_vision.alert_manager import update_alert_state


class PoseManagerNode(Node):

    def __init__(self):
        super().__init__('pose_manager_node')

        self.bridge = CvBridge()

        self.model = YOLO('/home/jetson/ws_1/yolov8n-pose.pt')
        self.model.fuse = lambda *args, **kwargs: self.model

        self.frame_count = {
            'front': 0,
            'back': 0
        }

        self.skip_frames = 6

        self.camera_states = {
            'front': self.create_camera_state('front'),
            'back': self.create_camera_state('back')
        }

        self.create_subscription(
            Image,
            '/camera/front/image_raw',
            lambda msg: self.image_callback(msg, 'front'),
            10
        )

        self.create_subscription(
            Image,
            '/camera/back/image_raw',
            lambda msg: self.image_callback(msg, 'back'),
            10
        )

        self.alert_pubs = {
            'front': self.create_publisher(String, '/vision/front/passenger_alert', 10),
            'back': self.create_publisher(String, '/vision/back/passenger_alert', 10),
        }

        self.count_pubs = {
            'front': self.create_publisher(Int32, '/vision/front/passenger_count', 10),
            'back': self.create_publisher(Int32, '/vision/back/passenger_count', 10),
        }

        self.get_logger().info('Pose Manager Node Started')

    def create_camera_state(self, name):
        save_dir = os.path.join(
            os.path.expanduser('~'),
            'person_logs',
            name
        )

        os.makedirs(save_dir, exist_ok=True)

        return {
            'name': name,
            'save_dir': save_dir,
            'save_count': 0,

            'standing_start_time': None,
            'standing_image_saved': False,
            'standing_confirm_time': 2.0,

            'hand_outside_start_time': None,
            'hand_image_saved': False,
            'hand_confirm_time': 2.0,

            'hip_standing_line': 260,
            'safe_left': 120,
            'safe_right': 520,
        }

    def image_callback(self, msg, camera_name):

        state = self.camera_states[camera_name]

        self.frame_count[camera_name] += 1

        if self.frame_count[camera_name] % self.skip_frames != 0:
            return

        frame = self.bridge.imgmsg_to_cv2(
            msg,
            desired_encoding='bgr8'
        )

        frame = cv2.resize(frame, (640, 384))

        # torch.cuda.empty_cache()

        results = self.model(
            frame,
            imgsz=320,
            conf=0.65,
            device=0,
            verbose=False
        )

        person_count = self.count_persons(results)

        is_standing = False
        for result in results:
            if detect_standing_from_state(self, state, result):
                is_standing = True
                break

        is_arm_outside = False
        for result in results:
            if detect_arm_outside_from_state(self, state, result):
                is_arm_outside = True
                break

        final_alert, alert, alert_hand, standing_duration, hand_duration = update_alert_state_from_state(
            state,
            is_standing,
            is_arm_outside
        )

        if len(results) > 0:
            annotated_frame = results[0].plot()
        else:
            annotated_frame = frame

        annotated_frame = draw_overlay(
            annotated_frame,
            final_alert,
            person_count,
            state['safe_left'],
            state['safe_right'],
            state['hip_standing_line']
        )

        if alert == 'STANDING' and not state['standing_image_saved']:

            state['save_count'] += 1

            filepath = save_alert_image(
                state['save_dir'],
                state['save_count'],
                'STANDING_ALERT',
                person_count,
                annotated_frame
            )

            self.get_logger().info(
                f'[{camera_name}] STANDING_ALERT saved: {filepath} | persons={person_count}'
            )

            state['standing_image_saved'] = True

        if alert_hand == 'ARM_OUTSIDE' and not state['hand_image_saved']:

            state['save_count'] += 1

            filepath = save_alert_image(
                state['save_dir'],
                state['save_count'],
                'HAND_OUTSIDE_ALERT',
                person_count,
                annotated_frame
            )

            self.get_logger().info(
                f'[{camera_name}] HAND_OUTSIDE_ALERT saved: {filepath} | persons={person_count}'
            )

            state['hand_image_saved'] = True

        self.alert_pubs[camera_name].publish(String(data=final_alert))
        self.count_pubs[camera_name].publish(Int32(data=person_count))

        self.get_logger().info(
            f'[{camera_name}] FINAL_ALERT={final_alert} | '
            f'persons={person_count} | '
            f'standing_time={standing_duration:.1f}s | '
            f'hand_time={hand_duration:.1f}s',
            throttle_duration_sec=1.0
        )

    def count_persons(self, results):
        person_count = 0

        for result in results:
            if result.boxes is None:
                continue

            for box in result.boxes:
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                if cls_id == 0 and conf >= 0.65:
                    person_count += 1

        return person_count


def detect_standing_from_state(node, state, result):
    original_hip_line = node.hip_standing_line if hasattr(node, 'hip_standing_line') else None

    node.hip_standing_line = state['hip_standing_line']
    detected = detect_standing(node, result)

    if original_hip_line is not None:
        node.hip_standing_line = original_hip_line

    return detected


def detect_arm_outside_from_state(node, state, result):
    original_safe_left = node.safe_left if hasattr(node, 'safe_left') else None
    original_safe_right = node.safe_right if hasattr(node, 'safe_right') else None

    node.safe_left = state['safe_left']
    node.safe_right = state['safe_right']

    detected = detect_arm_outside(node, result)

    if original_safe_left is not None:
        node.safe_left = original_safe_left

    if original_safe_right is not None:
        node.safe_right = original_safe_right

    return detected


def update_alert_state_from_state(state, is_standing, is_arm_outside):
    import time

    alert_standing = 'NORMAL'
    alert_hand = 'NORMAL'

    standing_duration = 0.0
    hand_duration = 0.0

    if is_standing:
        if state['standing_start_time'] is None:
            state['standing_start_time'] = time.time()
            state['standing_image_saved'] = False

        standing_duration = time.time() - state['standing_start_time']

        if standing_duration >= state['standing_confirm_time']:
            alert_standing = 'STANDING'
    else:
        state['standing_start_time'] = None
        state['standing_image_saved'] = False

    if is_arm_outside:
        if state['hand_outside_start_time'] is None:
            state['hand_outside_start_time'] = time.time()
            state['hand_image_saved'] = False

        hand_duration = time.time() - state['hand_outside_start_time']

        if hand_duration >= state['hand_confirm_time']:
            alert_hand = 'ARM_OUTSIDE'
    else:
        state['hand_outside_start_time'] = None
        state['hand_image_saved'] = False

    final_alert = 'NORMAL'

    if alert_standing == 'STANDING':
        final_alert = 'WARNING_STANDING'

    if alert_hand == 'ARM_OUTSIDE':
        final_alert = 'DANGER_ARM_OUTSIDE'

    return final_alert, alert_standing, alert_hand, standing_duration, hand_duration


def main(args=None):
    rclpy.init(args=args)

    node = PoseManagerNode()

    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()