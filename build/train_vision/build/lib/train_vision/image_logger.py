import os
import cv2
from datetime import datetime


def save_alert_image(
    save_dir,
    save_count,
    alert_name,
    person_count,
    frame
):

    timestamp = datetime.now().strftime(
        '%Y%m%d_%H%M%S'
    )

    filename = (
        f'{save_count}_{alert_name}_persons_{person_count}_{timestamp}.jpg'
    )

    filepath = os.path.join(
        save_dir,
        filename
    )

    cv2.imwrite(filepath, frame)

    return filepath