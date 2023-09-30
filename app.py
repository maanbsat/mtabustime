#!/usr/bin/env python

import os
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

from dotenv import load_dotenv
import requests
from flask import Flask, Response, render_template

TEMPLATE_PATH = Path("bustime-template.svg")

load_dotenv()
app = Flask(__name__)


def get_bus_times():
    URL = "http://bustime.mta.info/api/siri/stop-monitoring.json"
    res = requests.get(
        URL,
        params={
            "key": os.environ.get("MTA_API_KEY"),
            "version": 2,
            "MonitoringRef": os.environ.get("STOP_ID"),
            "LineRef": os.environ.get("LINE_REF"),
            "StopMonitoringDetailLevel": "minimum",
        },
    )
    res.raise_for_status()
    res = res.json()
    timestamp = datetime.fromisoformat(
        res["Siri"]["ServiceDelivery"]["ResponseTimestamp"]
    )

    times = []
    for b in res["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"][0][
        "MonitoredStopVisit"
    ]:
        bus = b["MonitoredVehicleJourney"]["MonitoredCall"]
        if "ExpectedArrivalTime" not in bus:
            continue
        t = datetime.fromisoformat(bus["ExpectedArrivalTime"])
        time = int(round((t - timestamp) / timedelta(minutes=1), 0))
        times.append(time)

    return times


@app.route("/bus_display")
def bus_display():
    bustimes = get_bus_times()

    ns = {"svg": "http://www.w3.org/2000/svg"}
    template = ET.parse(TEMPLATE_PATH)
    root = template.getroot()

    for i, textbox in enumerate(["Time-1", "Time-2", "Time-3", "Time-4"]):
        txt = root.find(f".//svg:text[@id='{textbox}']", ns)
        if i < len(bustimes):
            txt.text = str(bustimes[i])
            if len(txt.text) > 1:
                txt.attrib["x"] = "329.347px"
        else:
            txt.text = None

    res = ET.tostring(root, encoding="unicode", xml_declaration=True)
    return Response(res, content_type="image/svg+xml")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    print(get_bus_times())

