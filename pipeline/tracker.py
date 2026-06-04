from __future__ import annotations

from dataclasses import dataclass

import supervision as sv


@dataclass
class TrackedPerson:

    visitor_id: str

    tracker_id: int

    bbox: tuple[int, int, int, int]

    confidence: float


class VisitorTracker:

    def __init__(self):

        self.tracker = sv.ByteTrack()

        self.id_map = {}

        self.next_visitor = 1

    def update(
        self,
        detections: sv.Detections,
    ) -> list[TrackedPerson]:

        tracked = self.tracker.update_with_detections(
            detections
        )

        output = []

        for i in range(len(tracked)):

            tracker_id = int(
                tracked.tracker_id[i]
            )

            if tracker_id not in self.id_map:

                visitor_id = (
                    f"VIS_{self.next_visitor:06d}"
                )

                self.id_map[
                    tracker_id
                ] = visitor_id

                self.next_visitor += 1

            visitor_id = self.id_map[
                tracker_id
            ]

            x1, y1, x2, y2 = (
                tracked.xyxy[i]
            )

            output.append(
                TrackedPerson(
                    visitor_id=visitor_id,
                    tracker_id=tracker_id,
                    bbox=(
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2),
                    ),
                    confidence=float(
                        tracked.confidence[i]
                    ),
                )
            )

        return output