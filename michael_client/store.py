"""
Created by Michael Wilson, Senior Software Engineer
9/09/2025
"""

from __future__ import annotations
import json, sqlite3
from typing import Any, Dict, Iterable
import pandas as pd

class michaeltore:
    def __init__(self, path: str = "michael_data.db"):
        self.path = path
        self._init()

    def _init(self):
        with sqlite3.connect(self.path) as cx:
            cx.execute("PRAGMA journal_mode=WAL")
            cx.execute("""
              CREATE TABLE IF NOT EXISTS devices (
                id TEXT PRIMARY KEY,
                name TEXT,
                type TEXT,
                status TEXT,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                last_seen TEXT,
                battery_level REAL,
                firmware_version TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
              )
            """)
            cx.execute("""
              CREATE TABLE IF NOT EXISTS tracks (
                id TEXT PRIMARY KEY,
                device_id TEXT,
                start_time TEXT,
                end_time TEXT,
                total_distance REAL,
                average_speed REAL,
                max_speed REAL,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (device_id) REFERENCES devices(id)
              )
            """)
            cx.execute("""
              CREATE TABLE IF NOT EXISTS track_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id TEXT,
                timestamp TEXT,
                latitude REAL, longitude REAL, altitude REAL,
                speed REAL, heading REAL,
                FOREIGN KEY (track_id) REFERENCES tracks(id)
              )
            """)
            cx.execute("""
              CREATE TABLE IF NOT EXISTS detections (
                id TEXT PRIMARY KEY,
                device_id TEXT,
                timestamp TEXT,
                detection_type TEXT,
                confidence REAL,
                latitude REAL,
                longitude REAL,
                altitude REAL,
                bbox_x REAL, bbox_y REAL, bbox_width REAL, bbox_height REAL,
                metadata TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (device_id) REFERENCES devices(id)
              )
            """)
            # indices
            cx.execute("CREATE INDEX IF NOT EXISTS idx_det_time ON detections(timestamp)")
            cx.execute("CREATE INDEX IF NOT EXISTS idx_det_type ON detections(detection_type)")
            cx.execute("CREATE INDEX IF NOT EXISTS idx_det_device ON detections(device_id)")

    def save_devices(self, devices: Iterable[Dict[str, Any]]):
        with sqlite3.connect(self.path) as cx:
            for d in devices:
                loc = d.get("location") or {}
                cx.execute("""
                  INSERT INTO devices (id,name,type,status,latitude,longitude,altitude,
                                       last_seen,battery_level,firmware_version,metadata,updated_at)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?,datetime('now'))
                  ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    type=excluded.type,
                    status=excluded.status,
                    latitude=excluded.latitude,
                    longitude=excluded.longitude,
                    altitude=excluded.altitude,
                    last_seen=excluded.last_seen,
                    battery_level=excluded.battery_level,
                    firmware_version=excluded.firmware_version,
                    metadata=excluded.metadata,
                    updated_at=datetime('now')
                """, (
                    d.get("id"), d.get("name"), d.get("type"), d.get("status"),
                    loc.get("latitude"), loc.get("longitude"), loc.get("altitude"),
                    d.get("lastSeen"), d.get("batteryLevel"), d.get("firmwareVersion"),
                    json.dumps(d.get("metadata") or {})
                ))

    def save_tracks(self, tracks: Iterable[Dict[str, Any]]):
        with sqlite3.connect(self.path) as cx:
            for t in tracks:
                cx.execute("""
                  INSERT INTO tracks (id, device_id, start_time, end_time, total_distance,
                                      average_speed, max_speed, metadata)
                  VALUES (?,?,?,?,?,?,?,?)
                  ON CONFLICT(id) DO UPDATE SET
                    device_id=excluded.device_id,
                    start_time=excluded.start_time,
                    end_time=excluded.end_time,
                    total_distance=excluded.total_distance,
                    average_speed=excluded.average_speed,
                    max_speed=excluded.max_speed,
                    metadata=excluded.metadata
                """, (
                    t.get("id"), t.get("deviceId"), t.get("startTime"), t.get("endTime"),
                    t.get("totalDistance"), t.get("averageSpeed"), t.get("maxSpeed"),
                    json.dumps(t.get("metadata") or {}),
                ))
                # track points
                for p in (t.get("points") or []):
                    loc = p.get("location") or {}
                    cx.execute("""
                      INSERT INTO track_points (track_id, timestamp, latitude, longitude, altitude, speed, heading)
                      VALUES (?,?,?,?,?,?,?)
                    """, (
                        t.get("id"), p.get("timestamp"), loc.get("latitude"),
                        loc.get("longitude"), loc.get("altitude"),
                        p.get("speed"), p.get("heading")
                    ))

    def save_detections(self, detections: Iterable[Dict[str, Any]]):
        with sqlite3.connect(self.path) as cx:
            for det in detections:
                loc = det.get("location") or {}
                bb = det.get("boundingBox") or {}
                cx.execute("""
                  INSERT INTO detections (id,device_id,timestamp,detection_type,confidence,
                    latitude,longitude,altitude,bbox_x,bbox_y,bbox_width,bbox_height,metadata)
                  VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                  ON CONFLICT(id) DO NOTHING
                """, (
                    det.get("id"), det.get("deviceId"), det.get("timestamp"),
                    det.get("detectionType"), det.get("confidence"),
                    loc.get("latitude"), loc.get("longitude"), loc.get("altitude"),
                    bb.get("x"), bb.get("y"), bb.get("width"), bb.get("height"),
                    json.dumps(det.get("metadata") or {})
                ))

    def recent_detection_analytics(self, days: int = 30) -> pd.DataFrame:
        q = f"""
        SELECT
          detection_type,
          DATE(timestamp) AS date,
          AVG(confidence) AS avg_confidence,
          COUNT(*) AS detection_count,
          device_id
        FROM detections
        WHERE timestamp >= datetime('now', '-{days} days')
        GROUP BY detection_type, DATE(timestamp), device_id
        ORDER BY date DESC
        """
        with sqlite3.connect(self.path) as cx:
            return pd.read_sql_query(q, cx)

    def detection_points(self, limit: int = 1000) -> pd.DataFrame:
        q = f"""
        SELECT id, device_id, timestamp, detection_type, confidence,
               latitude, longitude
        FROM detections
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT {limit}
        """
        with sqlite3.connect(self.path) as cx:
            return pd.read_sql_query(q, cx)
