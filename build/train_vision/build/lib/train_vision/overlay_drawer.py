import cv2


def draw_overlay(frame, final_alert, person_count, safe_left, safe_right, hip_line):
    annotated_frame = frame

    cv2.line(annotated_frame, (safe_left, 0), (safe_left, 384), (0, 255, 255), 2)
    cv2.line(annotated_frame, (safe_right, 0), (safe_right, 384), (0, 255, 255), 2)
    cv2.line(annotated_frame, (0, hip_line), (640, hip_line), (255, 0, 0), 2)

    cv2.putText(annotated_frame, f'FINAL ALERT: {final_alert}', (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.putText(annotated_frame, f'Persons: {person_count}', (20, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    return annotated_frame