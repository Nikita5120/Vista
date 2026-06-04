from __future__ import annotations

import cv2
import numpy as np


class StaffClassifier:

    def __init__(
        self,
        lower_hsv,
        upper_hsv,
        threshold=0.15,
    ):
        self.lower_hsv = np.array(
            lower_hsv,
            dtype=np.uint8,
        )

        self.upper_hsv = np.array(
            upper_hsv,
            dtype=np.uint8,
        )

        self.threshold = threshold

    def is_staff(
        self,
        frame,
        bbox,
    ) -> bool:

        x1, y1, x2, y2 = bbox

        h = y2 - y1

        torso_y1 = y1 + int(h * 0.2)
        torso_y2 = y1 + int(h * 0.7)

        roi = frame[
            torso_y1:torso_y2,
            x1:x2,
        ]

        if roi.size == 0:
            return False

        hsv = cv2.cvtColor(
            roi,
            cv2.COLOR_BGR2HSV,
        )

        mask = cv2.inRange(
            hsv,
            self.lower_hsv,
            self.upper_hsv,
        )

        ratio = (
            np.count_nonzero(mask)
            / mask.size
        )

        return ratio >= self.threshold