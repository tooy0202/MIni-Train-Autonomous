import time


def update_alert_state(node, is_standing, is_arm_outside):
    alert_standing = 'NORMAL'
    alert_hand = 'NORMAL'

    standing_duration = 0.0
    hand_duration = 0.0

    # STANDING timer
    if is_standing:
        if node.standing_start_time is None:
            node.standing_start_time = time.time()
            node.standing_image_saved = False

        standing_duration = time.time() - node.standing_start_time

        if standing_duration >= node.standing_confirm_time:
            alert_standing = 'STANDING'
    else:
        node.standing_start_time = None
        node.standing_image_saved = False

    # ARM OUTSIDE timer
    if is_arm_outside:
        if node.hand_outside_start_time is None:
            node.hand_outside_start_time = time.time()
            node.hand_image_saved = False

        hand_duration = time.time() - node.hand_outside_start_time

        if hand_duration >= node.hand_confirm_time:
            alert_hand = 'ARM_OUTSIDE'
    else:
        node.hand_outside_start_time = None
        node.hand_image_saved = False

    # priority
    final_alert = 'NORMAL'

    if alert_standing == 'STANDING':
        final_alert = 'WARNING_STANDING'

    if alert_hand == 'ARM_OUTSIDE':
        final_alert = 'DANGER_ARM_OUTSIDE'

    return final_alert, alert_standing, alert_hand, standing_duration, hand_duration