#อันนี้ถ้าเห็นแค่ไหล่สโพงก็บอกว่ายืนแล้ว
def detect_standing(self, result):

    if result.keypoints is None:
        return False

    keypoints = result.keypoints.data

    if keypoints is None or len(keypoints) == 0:
        return False

    KEYPOINT_CONF = 0.4

    for person in keypoints:

        if person.shape[0] < 17:
            continue

        left_shoulder = person[5]
        right_shoulder = person[6]

        left_hip = person[11]
        right_hip = person[12]

        shoulders = []
        hips = []

        for p in [left_shoulder, right_shoulder]:
            if float(p[2]) > KEYPOINT_CONF:
                shoulders.append(p)

        for p in [left_hip, right_hip]:
            if float(p[2]) > KEYPOINT_CONF:
                hips.append(p)

        if len(shoulders) == 0 or len(hips) == 0:
            continue

        shoulder_y = sum([float(p[1]) for p in shoulders]) / len(shoulders)
        hip_y = sum([float(p[1]) for p in hips]) / len(hips)

        torso_height = abs(hip_y - shoulder_y)

        # debug
        self.get_logger().info(
            f'torso_height={torso_height:.1f}',
            throttle_duration_sec=1.0
        )
        #MAX สโพค
        HIP_STANDING_LINE = self.hip_standing_line
        #MAX ไหล่
        TORSO_STANDING_THRESHOLD = 130
        #สโพค
        if hip_y > HIP_STANDING_LINE:
            continue
        #ไหล่
        if torso_height > TORSO_STANDING_THRESHOLD:
            return True

    return False