#---------------------------------------------------
#ตรวจจับถ้ามือยื่นออกมานอกกล้อง
def detect_arm_outside(self, result):

    if result.keypoints is None:
        return False

    keypoints = result.keypoints.data

    if keypoints is None or len(keypoints) == 0:
        return False

    KEYPOINT_CONF = 0.4
#กำหนด safesone ระหว่าง 120-520 px ถ้าทั้งหมดมี 640
    SAFE_LEFT = 120
    SAFE_RIGHT = 520
#----------------------------------------------
    for person in keypoints:

        if person.shape[0] < 17:
            continue

        left_wrist = person[9]
        right_wrist = person[10]

        wrists = [
            left_wrist,
            right_wrist
        ]

        for wrist in wrists:

            conf = float(wrist[2])

            if conf < KEYPOINT_CONF:
                continue

            wrist_x = float(wrist[0])

            # debug
            self.get_logger().info(
                f'wrist_x={wrist_x:.1f}',
                throttle_duration_sec=1.0
            )

            if wrist_x < SAFE_LEFT:
                return True

            if wrist_x > SAFE_RIGHT:
                return True

    return False
#-------------------------------------------------------------------