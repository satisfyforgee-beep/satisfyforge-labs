#!/usr/bin/env python3
"""Set a useful edit-mode Studio camera on a Rojo-built Rift Raiders place.

Rojo's minimal place otherwise opens pointed at an empty sky. The imported
Modern City model is at its original template coordinates until Play starts,
when ModernCityIntegration moves it to the downtown gameplay location.
"""
import argparse
import math
import xml.etree.ElementTree as ET
from pathlib import Path

CAMERA_REF = "SFModernCityEditorCamera"
CAMERA_POSITION = (740.0, 145.0, 420.0)
CAMERA_TARGET = (720.0, 52.0, 195.0)


def normalize(v):
    length = math.sqrt(sum(x * x for x in v))
    return tuple(x / length for x in v)


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def frame(parent, name, pos, look_at=None):
    cf = ET.SubElement(parent, "CoordinateFrame", {"name": name})
    if look_at:
        forward = normalize(tuple(b - a for a, b in zip(pos, look_at)))
        right = normalize(cross(forward, (0.0, 1.0, 0.0)))
        up = cross(right, forward)
        cols = (right, up, tuple(-x for x in forward))
    else:
        cols = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
    for axis, value in zip("XYZ", pos):
        ET.SubElement(cf, axis).text = f"{value:.9g}"
    for row in range(3):
        for col in range(3):
            ET.SubElement(cf, f"R{row}{col}").text = f"{cols[col][row]:.9g}"


def patch(path):
    tree = ET.parse(path)
    root = tree.getroot()
    workspace = next(x for x in root.findall("Item") if x.get("class") == "Workspace")
    props = workspace.find("Properties")
    for x in list(props):
        if x.get("name") == "CurrentCamera":
            props.remove(x)
    ET.SubElement(props, "Ref", {"name": "CurrentCamera"}).text = CAMERA_REF
    for x in list(workspace):
        if x.tag == "Item" and x.get("referent") == CAMERA_REF:
            workspace.remove(x)
    cam = ET.SubElement(workspace, "Item", {"class": "Camera", "referent": CAMERA_REF})
    cp = ET.SubElement(cam, "Properties")
    frame(cp, "CFrame", CAMERA_POSITION, CAMERA_TARGET)
    frame(cp, "Focus", CAMERA_TARGET)
    ET.SubElement(cp, "string", {"name": "Name"}).text = "Camera"
    ET.SubElement(cp, "float", {"name": "FieldOfView"}).text = "70"
    ET.SubElement(cp, "token", {"name": "CameraType"}).text = "0"
    ET.SubElement(cp, "Ref", {"name": "CameraSubject"}).text = "null"
    tree.write(path, encoding="utf-8", xml_declaration=True)
    print(f"Set edit-mode Modern City camera in {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("place", type=Path)
    args = parser.parse_args()
    patch(args.place)
