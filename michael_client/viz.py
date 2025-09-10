"""
Created by Michael Wilson, Senior Software Engineer
9/09/2025
"""

from __future__ import annotations
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class MichaelViz:
    @staticmethod
    def dashboard(df: pd.DataFrame) -> go.Figure:
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Daily Detection Count", "Confidence Distribution",
                "Detection Types", "Device Activity"
            ),
            specs=[[{}, {}], [{}, {}]]
        )
        daily = df.groupby("date")["detection_count"].sum().reset_index()
        fig.add_scatter(x=daily["date"], y=daily["detection_count"], mode="lines+markers", row=1, col=1)
        fig.add_histogram(x=df["avg_confidence"], nbinsx=20, row=1, col=2)

        by_type = df.groupby("detection_type")["detection_count"].sum()
        fig.add_bar(x=by_type.index, y=by_type.values, row=2, col=1)

        by_device = df.groupby("device_id")["detection_count"].sum()
        fig.add_bar(x=by_device.index, y=by_device.values, row=2, col=2)

        fig.update_layout(height=600, showlegend=False, title_text="Detections (last window)")
        return fig

    @staticmethod
    def map(points: pd.DataFrame) -> go.Figure:
        fig = go.Figure()
        for dtype, chunk in points.groupby("detection_type"):
            fig.add_trace(go.Scattermapbox(
                lat=chunk["latitude"], lon=chunk["longitude"],
                mode="markers", marker=dict(size=8), name=str(dtype),
                hovertemplate="<b>%{text}</b><br>Conf: %{customdata[0]:.2f}<br>"
                              "Device: %{customdata[1]}<br>Time: %{customdata[2]}<extra></extra>",
                text=chunk["detection_type"],
                customdata=list(zip(chunk["confidence"], chunk["device_id"], chunk["timestamp"]))
            ))
        lat_center = float(points["latitude"].mean()) if not points.empty else 0.0
        lon_center = float(points["longitude"].mean()) if not points.empty else 0.0
        fig.update_layout(
            mapbox=dict(style="open-street-map", center=dict(lat=lat_center, lon=lon_center), zoom=10),
            title="Detection Locations",
            height=600
        )
        return fig
