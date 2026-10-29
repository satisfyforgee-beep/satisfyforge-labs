#!/usr/bin/env python3
"""Extract a script-free art-only race car from Roblox Studio's Racing template.

Keeps only original MeshPart visual geometry and SurfaceAppearance. Physics
scripts, audio, constraints, welds, networking and gameplay UI are not reused.
"""
import argparse
import copy
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0,str(Path(__file__).resolve().parent))
from extract_official_city import sanitize, set_name

def generate(source, destination):
    tree=ET.parse(source)
    car=next((x for x in tree.getroot().iter('Item') if
       x.get('class')=='Model' and
       x.findtext('./Properties/string[@name="Name"]')=='Car'),None)
    if car is None:raise RuntimeError("Racing template Car model not found")
    root=ET.Element('roblox',{'version':'4'})
    ET.SubElement(root,'External').text='null'
    ET.SubElement(root,'External').text='nil'
    art=ET.SubElement(root,'Item',{'class':'Model','referent':'SF_Race_Art_Model'})
    props=ET.SubElement(art,'Properties')
    ET.SubElement(props,'string',{'name':'Name'}).text='OfficialRacingCarVisual'
    count=0
    for section in car.findall('Item'):
        label=section.findtext('./Properties/string[@name="Name"]')
        if label not in ('Body','Wheels'):continue
        for item in section.iter('Item'):
            if item.get('class')!='MeshPart':continue
            part=copy.deepcopy(item)
            # Retain legitimate SurfaceAppearance children; discard all other
            # object references and behavior. Original mesh asset IDs remain.
            for child in list(part):
                if child.tag=='Item' and child.get('class')!='SurfaceAppearance':
                    part.remove(child)
            sanitize(part)
            p=part.find('Properties')
            for name,value in [
                ('Anchored','true'),('CanCollide','false'),
                ('CanTouch','false'),('CanQuery','false')
            ]:
                node=next((v for v in p if v.get('name')==name),None)
                if node is None:node=ET.SubElement(p,'bool',{'name':name})
                node.text=value
            set_name(part,'Race Art '+(part.findtext('./Properties/string[@name="Name"]') or 'Mesh'))
            part.set('referent','SF_Race_Mesh_'+str(count))
            art.append(part)
            count+=1
    if count<25:raise RuntimeError(f"Racing car expected 25+ detailed mesh parts; got {count}")
    destination.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(destination,encoding='utf-8',xml_declaration=True)
    print(f"Extracted {count} 3D mesh parts into {destination} ({destination.stat().st_size:,} bytes)")

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('source',type=Path)
    ap.add_argument('destination',type=Path)
    a=ap.parse_args()
    generate(a.source,a.destination)
