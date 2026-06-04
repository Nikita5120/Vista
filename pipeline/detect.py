from __future__ import annotations

import time
import cv2
import requests

from ultralytics import YOLO
import supervision as sv

from pipeline.tracker import VisitorTracker
from pipeline.zone_mapper import ZoneMapper
from pipeline.staff_classifier import StaffClassifier

from pipeline.emit import (
    make_event,
    write_event,
)

API_URL = "http://127.0.0.1:8000/events/ingest"


class StoreDetector:

    def __init__(self):

        self.model = YOLO("yolov8n.pt")

        self.tracker = VisitorTracker()

        self.mapper = ZoneMapper(
            "data/store_layout.json"
        )

        # Zone analytics
        self.previous_zone = {}
        self.person_state = {}

        # Entry / Exit analytics
        self.entry_state = {}
        self.entry_members = {}

        # Billing analytics
        self.billing_state = {}
        self.queue_members = set()

    

    
    def send_event(self, event):

        try:

            payload = {
                "events": [
                    event.model_dump(
                        mode="json"
                    )
                ]
            }

            response = requests.post(
                API_URL,
                json=payload,
                timeout=3,
            )

            print(
                "API:",
                response.status_code
            )

            print(
                response.text
            )

        except Exception as e:

            print(
                "API ERROR:",
                str(e)
            )

    def process_video(
        self,
        video_path,
        store_id,
        camera_id,
    ):

        cap = cv2.VideoCapture(video_path)

        print(f"Opening video: {video_path}")
        print(f"Opened: {cap.isOpened()}")

        if not cap.isOpened():
            print("ERROR: Could not open video.")
            return

        frame_count = 0
        while True:

            ret, frame = cap.read()

            if not ret:
                print("End of video")
                break

            frame_count += 1

            result = self.model(
                frame,
                classes=[0],
                verbose=False,
            )[0]

            detections = sv.Detections.from_ultralytics(result)

            tracked_people = self.tracker.update(detections)

            if frame_count % 30 == 0:
                print(
                    f"Frame={frame_count} "
                    f"Detections={len(detections)} "
                    f"Tracked={len(tracked_people)}"
                )

            # ── per-person loop ──────────────────────────────────────────
            for person in tracked_people:

                cx, cy = self.mapper.get_centroid(person.bbox)

                # ── ENTRY / EXIT tracking ────────────────────────────────
                if camera_id == "CAM_3_ENTRY":

                    ENTRY_LINE_X = 450

                    state = self.entry_state.get(person.visitor_id)
                    previous_x = state["x"] if state else None
                    last_event = state["last_event"] if state else None

                    print(
                        f"{person.visitor_id} "
                        f"prev_x={previous_x} "
                        f"cx={cx}"
                    )

                    if previous_x is not None:

                        if (
                            previous_x > ENTRY_LINE_X
                            and cx <= ENTRY_LINE_X
                            and last_event != "ENTRY"
                        ):
                            entry_event = make_event(
                                store_id=store_id,
                                camera_id=camera_id,
                                visitor_id=person.visitor_id,
                                event_type="ENTRY",
                                confidence=person.confidence,
                                session_seq=1,
                                zone_id=None,
                            )
                            write_event(entry_event, "events.jsonl")
                            self.send_event(entry_event)
                            print(f"{person.visitor_id} ENTRY")
                            self.entry_state[person.visitor_id] = {
                                "x": cx,
                                "last_event": "ENTRY",
                            }

                        elif (
                            previous_x < ENTRY_LINE_X
                            and cx >= ENTRY_LINE_X
                            and last_event != "EXIT"
                        ):
                            exit_event = make_event(
                                store_id=store_id,
                                camera_id=camera_id,
                                visitor_id=person.visitor_id,
                                event_type="EXIT",
                                confidence=person.confidence,
                                session_seq=1,
                                zone_id=None,
                            )
                            write_event(exit_event, "events.jsonl")
                            self.send_event(exit_event)
                            print(f"{person.visitor_id} EXIT")
                            self.entry_state[person.visitor_id] = {
                                "x": cx,
                                "last_event": "EXIT",
                            }

                        else:
                            # no crossing — just update position
                            self.entry_state[person.visitor_id] = {
                                "x": cx,
                                "last_event": last_event,
                            }

                    else:
                        # first time we see this visitor
                        self.entry_state[person.visitor_id] = {
                            "x": cx,
                            "last_event": None,
                        }

                # ── BILLING QUEUE tracking ───────────────────────────────
                if camera_id == "CAM_5_BILLING":

                    QUEUE_LINE_X = 700

                    prev_x = self.billing_state.get(person.visitor_id)

                    if prev_x is not None:

                        if (
                            prev_x < QUEUE_LINE_X
                            and cx >= QUEUE_LINE_X
                            and person.visitor_id
                                not in self.queue_members
                        ):
                            queue_event = make_event(
                                store_id=store_id,
                                camera_id=camera_id,
                                visitor_id=person.visitor_id,
                                event_type="BILLING_QUEUE_JOIN",
                                confidence=person.confidence,
                                session_seq=1,
                                zone_id="BILLING",
                            )
                            write_event(queue_event, "events.jsonl")
                            self.send_event(queue_event)
                            self.queue_members.add(person.visitor_id)
                            print(f"{person.visitor_id} QUEUE_JOIN")

                    self.billing_state[person.visitor_id] = cx

                # ── ZONE tracking (floor cameras only) ──────────────────
                zone = None

                if camera_id != "CAM_3_ENTRY":
                    zone = self.mapper.get_zone(
                        store_id,
                        camera_id,
                        cx,
                        cy,
                    )

                previous = self.previous_zone.get(person.visitor_id)

                if (
                    camera_id != "CAM_3_ENTRY"
                    and zone is not None
                    and previous != zone
                ):
                    now = time.time()

                    # emit ZONE_EXIT + ZONE_DWELL for the zone being left
                    if person.visitor_id in self.person_state:

                        old_state = self.person_state[person.visitor_id]

                        dwell_ms = int(
                            (now - old_state["entered_at"]) * 1000
                        )

                        zone_exit_event = make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=person.visitor_id,
                            event_type="ZONE_EXIT",
                            confidence=person.confidence,
                            session_seq=1,
                            zone_id=old_state["zone"],
                        )
                        write_event(zone_exit_event, "events.jsonl")
                        self.send_event(zone_exit_event)

                        dwell_event = make_event(
                            store_id=store_id,
                            camera_id=camera_id,
                            visitor_id=person.visitor_id,
                            event_type="ZONE_DWELL",
                            confidence=person.confidence,
                            session_seq=1,
                            zone_id=old_state["zone"],
                            dwell_ms=dwell_ms,
                        )
                        write_event(dwell_event, "events.jsonl")
                        self.send_event(dwell_event)

                    # emit ZONE_ENTER for the new zone
                    enter_event = make_event(
                        store_id=store_id,
                        camera_id=camera_id,
                        visitor_id=person.visitor_id,
                        event_type="ZONE_ENTER",
                        confidence=person.confidence,
                        session_seq=1,
                        zone_id=zone,
                    )
                    write_event(enter_event, "events.jsonl")
                    self.send_event(enter_event)

                    self.previous_zone[person.visitor_id] = zone
                    self.person_state[person.visitor_id] = {
                        "zone": zone,
                        "entered_at": now,
                    }

                    print(f"{person.visitor_id} entered {zone}")

                # ── draw bounding box and visitor id ─────────────────────
                x1, y1, x2, y2 = person.bbox

                cv2.rectangle(
                    frame,
                    (int(x1), int(y1)),
                    (int(x2), int(y2)),
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    str(person.visitor_id),
                    (int(x1), int(y1 - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

            # ── draw reference lines (outside person loop, once per frame)
            if camera_id == "CAM_3_ENTRY":

                ENTRY_LINE_X = 450

                cv2.line(
                    frame,
                    (ENTRY_LINE_X, 0),
                    (ENTRY_LINE_X, frame.shape[0]),
                    (255, 0, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    "ENTRY LINE",
                    (ENTRY_LINE_X + 10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 0, 0),
                    2,
                )

            if camera_id == "CAM_5_BILLING":

                QUEUE_LINE_X = 700

                cv2.line(
                    frame,
                    (QUEUE_LINE_X, 0),
                    (QUEUE_LINE_X, frame.shape[0]),
                    (0, 0, 255),
                    2,
                )

                cv2.putText(
                    frame,
                    "QUEUE",
                    (QUEUE_LINE_X + 10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )

            # ── display ──────────────────────────────────────────────────
            cv2.imshow("Store Analytics", frame)

            key = cv2.waitKey(1)

            if key & 0xFF == ord("q"):
                print("Stopped by user")
                break

        cap.release()
        cv2.destroyAllWindows()
        print("Video processing complete.")
