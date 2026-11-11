#!/usr/bin/env python3
"""Extract a SCRIPT-FREE, reusable official Roblox Modern City district.

Input: a local copy saved from Roblox Studio's own Modern City template.
Output: a curated .rbxmx model usable in Rojo, not the full 145 MB demo place.
Never redistribute third-party Toolbox scripts or the template's demo scripts.
"""
from __future__ import annotations
import argparse
import copy
import xml.etree.ElementTree as ET
from pathlib import Path

# Buildings from a continuous downtown block in the official template.
BUILDINGS = {
    "9_bldg", "12_bldg", "13_bldg", "14_bldg", "15_bldg",
    "30_bldg", "16_bldg", "17_bldg", "18_bldg", "19_Bldg",
    "20_bldg", "21_bldg", "58_BLDG",
}
STREET_FOLDERS = {
    "StreetMeshes", "Decals", "StreetLights", "Street_SetDressing",
    "StreetTrees", "BusStops", "StreetParts",
}
SCRIPTS = {"Script", "LocalScript", "ModuleScript", "UnionOperation"}
# Roblox Studio 2026 writes internal mesh cache blobs that older Rojo versions
# cannot round-trip (BinaryString -> NetAsset). They are not required when the
# official public MeshId and texture asset IDs are preserved.
INTERNAL_TAGS = {"BinaryString", "SharedString", "UniqueId", "SecurityCapabilities"}
INTERNAL_NAMES = {"SourceAssetId", "Capabilities", "DefinesCapabilities",
                  "SerializedOverrides", "HistoryId", "UniqueId"}
MIN_X, MAX_X = 600.0, 840.0
MIN_Z, MAX_Z = 85.0, 320.0


def name(item):
    p = item.find('./Properties/string[@name="Name"]')
    return p.text if p is not None else None


def set_name(item, value):
    p = item.find('./Properties/string[@name="Name"]')
    if p is None:
        p = ET.SubElement(item.find("Properties"), "string", {"name": "Name"})
    p.text = value


def coordinates(item):
    for part in item.iter("Item"):
        if part.get("class") not in {
            "Part", "MeshPart", "WedgePart", "CornerWedgePart",
            "UnionOperation", "SpawnLocation", "TrussPart",
        }:
            continue
        cf = part.find('./Properties/CoordinateFrame[@name="CFrame"]')
        if cf is None:
            continue
        try:
            yield (float(cf.findtext("X")), float(cf.findtext("Y")), float(cf.findtext("Z")))
        except (TypeError, ValueError):
            pass


def in_bounds(item):
    coords = list(coordinates(item))
    if not coords:
        return False
    x = sum(p[0] for p in coords) / len(coords)
    z = sum(p[2] for p in coords) / len(coords)
    return MIN_X <= x <= MAX_X and MIN_Z <= z <= MAX_Z


def sanitize(item):
    """Remove scripts, unsupported internal blobs, and union geometry caches."""
    props = item.find("Properties")
    if props is not None:
        for prop in list(props):
            if prop.tag in INTERNAL_TAGS or prop.get("name") in INTERNAL_NAMES:
                props.remove(prop)
    for child in list(item):
        if child.tag == "Item" and child.get("class") in SCRIPTS:
            item.remove(child)
        else:
            sanitize(child)


def filter_streets(item):
    """Keep complete street furniture models, but only within the downtown rectangle."""
    for child in list(item):
        if child.tag != "Item":
            continue
        if child.get("class") in SCRIPTS or not in_bounds(child):
            item.remove(child)
        else:
            sanitize(child)


def extract(source: Path, output: Path):
    out = ET.Element("roblox", {
        "xmlns:xmime": "http://www.w3.org/2005/05/xmlmime",
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "http://www.roblox.com/roblox.xsd",
        "version": "4",
    })
    ET.SubElement(out, "External").text = "null"
    ET.SubElement(out, "External").text = "nil"
    model = ET.SubElement(out, "Item", {"class": "Model", "referent": "SFOfficialModernCity"})
    props = ET.SubElement(model, "Properties")
    ET.SubElement(props, "string", {"name": "Name"}).text = "OfficialModernCityDistrict"
    ET.SubElement(props, "token", {"name": "LevelOfDetail"}).text = "1"
    count = {"buildings": 0, "streetGroups": 0, "streetModels": 0}
    ground_template = None
    stack = []
    in_city = False
    for event, item in ET.iterparse(source, events=("start", "end")):
        if event == "start":
            stack.append((item.tag, item.get("class")))
            continue
        if len(stack) == 5 and stack[1][1] == "Workspace" and \
           stack[2][1] == "Folder" and stack[3][1] == "Folder" and \
           item.tag == "Item":
            parent_name = stack[3][1]
            n = name(item)
            if item.get("class") == "Model" and n in BUILDINGS:
                if ground_template is None:
                    ground_template = next((copy.deepcopy(x) for x in item.iter("Item")
                        if x.get("class") == "Part" and not x.findall("./Item")), None)
                sanitize(item)
                set_name(item, "Official Building " + n)
                model.append(item)
                count["buildings"] += 1
            elif item.get("class") == "Folder" and n in STREET_FOLDERS:
                filter_streets(item)
                count["streetModels"] += len(item.findall("./Item"))
                if len(item.findall("./Item")):
                    model.append(item)
                    count["streetGroups"] += 1
            else:
                item.clear()
        stack.pop()
    # A curated template block omits the demo's terrain/baseplate. Without
    # this static road foundation, Studio edit mode shows floating buildings
    # against a cyan void. Keep it inside the imported Model so the runtime
    # city relocation moves it along with the buildings.
    assert ground_template is not None
    sanitize(ground_template)
    ground_template.set("referent", "SFModernCityGround")
    set_name(ground_template, "Modern City Asphalt Foundation")
    props = ground_template.find("Properties")
    def prop(name):
        return next(x for x in props if x.get("name") == name)
    size = prop("size")
    for axis, value in zip("XYZ", (360, 2, 390)):
        size.find(axis).text = str(value)
    cf = prop("CFrame")
    for axis, value in zip("XYZ", (720, -1, 200)):
        cf.find(axis).text = str(value)
    for row in range(3):
        for col in range(3):
            cf.find(f"R{row}{col}").text = "1" if row == col else "0"
    prop("Material").text = "1024"  # Enum.Material.Asphalt
    prop("Color3uint8").text = str((255<<24)|(67<<16)|(70<<8)|72)
    prop("Anchored").text = "true"
    prop("CanCollide").text = "true"
    prop("CanTouch").text = "false"
    prop("CastShadow").text = "false"
    prop("Transparency").text = "0"
    if any(x.get("name") == "MaterialVariantSerialized" for x in props):
        prop("MaterialVariantSerialized").text = ""
    model.append(ground_template)
    # Broken cross-model welds / refs must never point to missing referents.
    all_refs = {x.get("referent") for x in model.iter("Item")}
    for x in model.iter("Ref"):
        if x.text and x.text not in all_refs and x.text != "null":
            x.text = "null"
    assert count["buildings"] >= 10, count
    assert count["streetGroups"] >= 4, count
    assert not any(x.get("class") in SCRIPTS for x in model.iter("Item"))
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(out).write(output, encoding="utf-8", xml_declaration=True)
    print(f"Extracted official city assets: {count}; {output.stat().st_size / 1e6:.1f} MB")
    print("Original template: Roblox Studio Modern City (Roblox official template).")
    print("No third-party scripts or scripts of any kind included.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    extract(args.source, args.output)
