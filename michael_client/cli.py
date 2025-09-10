"""
Created by Michael Wilson, Senior Software Engineer
"""

from __future__ import annotations
import argparse, asyncio, logging
from datetime import datetime, timedelta
from .config import MichaelConfig
from .http import MichaelHTTP
from .gql import INTROSPECTION, GET_DEVICES, GET_TRACKS, GET_DETECTIONS, CREATE_EVENT
from .store import michaeltore
from .subs import michaelubs
from .viz import MichaelViz

LOG = logging.getLogger("michael")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
LOG.addHandler(handler)
LOG.setLevel(logging.INFO)

async def fetch_everything(cfg: MichaelConfig, store: michaeltore, hours: int = 24):
    start = datetime.datetime.now(datetime.timezone.utc) - timedelta(hours=hours)
    end = datetime.datetime.now(datetime.timezone.utc)
    async with MichaelHTTP(cfg) as http:
        LOG.info("Introspecting schema…")
        _ = await http.execute(INTROSPECTION)

        LOG.info("Loading devices…")
        devs = await http.execute(GET_DEVICES, {"limit": 100, "offset": 0})
        devices = (devs.get("data") or {}).get("devices") or []
        store.save_devices(devices)
        LOG.info("Saved %d devices", len(devices))

        LOG.info("Loading tracks (%dh)…", hours)
        tr = await http.execute(GET_TRACKS, {
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "limit": 100
        })
        tracks = (tr.get("data") or {}).get("tracks") or []
        store.save_tracks(tracks)
        LOG.info("Saved %d tracks (and points)", len(tracks))

        LOG.info("Loading detections (%dh)…", hours)
        dets = await http.execute(GET_DETECTIONS, {
            "startTime": start.isoformat(),
            "endTime": end.isoformat(),
            "limit": 1000,
            "minConfidence": 0.5
        })
        detections = (dets.get("data") or {}).get("detections") or []
        store.save_detections(detections)
        LOG.info("Saved %d detections", len(detections))

async def create_sample_event(cfg: MichaelConfig):
    payload = {
        "name": "Sample Detection Event",
        "type": "ANOMALY_DETECTED",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "deviceId": "sample-device-id",
        "location": {"latitude": 40.7128, "longitude": -74.0060, "altitude": 10.0},
        "metadata": {"source": "demo", "confidence": 0.85, "note": "Created from CLI"},
    }
    async with MichaelHTTP(cfg) as http:
        res = await http.execute(CREATE_EVENT, {"input": payload})
        evt = (res.get("data") or {}).get("createEvent")
        if not evt:
            raise SystemExit(f"Event creation failed: {res}")
        LOG.info("Created event id=%s type=%s", evt["id"], evt["type"])

async def run_subscriptions(cfg: MichaelConfig, min_conf: float = 0.7):
    async def on_det(d):
        LOG.info("Detection %-16s conf=%.2f device=%s time=%s",
                 d.get("detectionType"), float(d.get("confidence") or 0),
                 d.get("deviceId"), d.get("timestamp"))
    subs = michaelubs(cfg)
    await subs.detections(on_det, min_confidence=min_conf)

def run_analytics(store: michaeltore):
    df = store.recent_detection_analytics(days=30)
    if df.empty:
        LOG.info("No detection analytics available.")
        return
    fig = MichaelViz.dashboard(df)
    fig.write_html("detection_dashboard.html")
    LOG.info("Wrote detection_dashboard.html")

    pts = store.detection_points(limit=1000)
    if not pts.empty:
        mfig = MichaelViz.map(pts)
        mfig.write_html("detection_map.html")
        LOG.info("Wrote detection_map.html")

def _parse_cli(argv=None):
    p = argparse.ArgumentParser(description="Michael GraphQL client")
    p.add_argument("--token-id", default="", help="x-token-id")
    p.add_argument("--token-value", default="", help="x-token-value")
    p.add_argument("--db", default="michael_data.db", help="SQLite path")
    p.add_argument("--hours", type=int, default=24, help="Look back window for fetch")

    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("fetch", help="Fetch devices/tracks/detections and persist")
    sub.add_parser("event", help="Create a sample event")
    ssub = sub.add_parser("subscribe", help="Subscribe to live detections")
    ssub.add_argument("--min-confidence", type=float, default=0.7)
    sub.add_parser("analytics", help="Generate HTML dashboard + map (if data present)")
    return p.parse_args(argv)

def _cfg_from_args(args) -> MichaelConfig:
    return MichaelConfig(token_id=args.token_id, token_value=args.token_value)

def main(argv=None):
    args = _parse_cli(argv)
    cfg = _cfg_from_args(args)
    store = michaeltore(args.db)

    if args.cmd == "fetch":
        asyncio.run(fetch_everything(cfg, store, hours=args.hours))
    elif args.cmd == "event":
        asyncio.run(create_sample_event(cfg))
    elif args.cmd == "subscribe":
        asyncio.run(run_subscriptions(cfg, min_conf=args.min_confidence))
    elif args.cmd == "analytics":
        run_analytics(store)

if __name__ == "__main__":
    main()
