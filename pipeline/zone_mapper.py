from __future__ import annotations

import json

from pathlib import Path

from shapely.geometry import (
    Point,
    Polygon,
)


class ZoneMapper:

    def __init__(
        self,
        layout_file: str,
    ):

        self.layout = json.loads(
            Path(layout_file)
            .read_text(
                encoding="utf-8"
            )
        )

        self.zone_polygons = {}

        self._build_polygons()

    def _build_polygons(self):

        for store in self.layout["stores"]:

            store_id = store[
                "store_id"
            ]

            self.zone_polygons[
                store_id
            ] = {}

            for camera in store[
                "cameras"
            ]:

                camera_id = camera[
                    "camera_id"
                ]

                self.zone_polygons[
                    store_id
                ][camera_id] = {}

                for zone in camera[
                    "zones"
                ]:

                    polygon = Polygon(
                        zone["polygon"]
                    )

                    self.zone_polygons[
                        store_id
                    ][camera_id][
                        zone["zone_id"]
                    ] = polygon

    def get_zone(
        self,
        store_id: str,
        camera_id: str,
        x: int,
        y: int,
    ):

        point = Point(x, y)

        zones = self.zone_polygons[
            store_id
        ][camera_id]

        for zone_id, polygon in zones.items():

            if polygon.contains(point):

                return zone_id

        return None

    @staticmethod
    def get_centroid(
        bbox
    ):

        x1, y1, x2, y2 = bbox

        cx = int(
            (x1 + x2) / 2
        )

        cy = int(
            (y1 + y2) / 2
        )

        return cx, cy