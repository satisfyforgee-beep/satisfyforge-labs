#!/usr/bin/env python3
"""Extract a curated, script-free official Roblox Studio Suburban environment.

Original Roblox Suburban template buildings are detailed assemblies (mostly
Part/WedgePart), not MeshParts. The small selection preserves source geometry,
textures and colors, and discards every executable script and engine cache.
"""
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from extract_official_city import sanitize,set_name

SELECT={
    'Urban House Singe Story':('Suburban Single Story House',1),
    'Double Story Urban House':('Suburban Two Story House',1),
    'Convenience Store':('Suburban Convenience Market',1),
    'GarageBuilding':('Suburban Detailed Garage',1),
    'Gas Station':('Suburban Gas Station',1),
    'Playground':('Suburban Playground',1),
}
def generate(source,output):
    root=ET.Element('roblox',{'version':'4'})
    ET.SubElement(root,'External').text='null'
    ET.SubElement(root,'External').text='nil'
    wrapper=ET.SubElement(root,'Item',{'class':'Model','referent':'SFSuburbPack'})
    props=ET.SubElement(wrapper,'Properties')
    ET.SubElement(props,'string',{'name':'Name'}).text='OfficialSuburbanArchitecture'
    counts={}
    stack=[]
    for event,item in ET.iterparse(source,events=('start','end')):
        if event=='start':
            stack.append((item.tag,item.get('class')))
            continue
        if len(stack)==3 and stack[1][1]=='Workspace' and item.tag=='Item':
            name=item.findtext('./Properties/string[@name="Name"]')
            if name in SELECT and counts.get(name,0)<SELECT[name][1]:
                sanitize(item)
                # The 2026 template still references two old Roblox assets
                # that are archived/not found; keep the model geometry while
                # discarding only those broken texture assignments.
                bad_assets=('192488947','29242300')
                for desc in item.iter('Item'):
                    props=desc.find('Properties')
                    if props is None:continue
                    for prop in list(props):
                        if any(any(bad in (node.text or '') for bad in bad_assets)
                               for node in prop.iter()):
                            props.remove(prop)
                set_name(item,SELECT[name][0])
                # Preserve original interdependent Part/Wedge geometry while
                # disabling remote references to demos and game scripts.
                count=0
                for obj in item.iter('Item'):
                    if obj.get('class') in (
                        'Part','WedgePart','CornerWedgePart','MeshPart',
                        'UnionOperation','TrussPart','SpawnLocation'):
                        p=obj.find('Properties')
                        if p is not None:
                            anchored=next((x for x in p if x.get('name')=='Anchored'),None)
                            if anchored is None:
                                anchored=ET.SubElement(p,'bool',{'name':'Anchored'})
                            anchored.text='true'
                        count+=1
                item.set('referent','SFSuburbAsset_'+str(len(counts)))
                wrapper.append(item)
                counts[name]=counts.get(name,0)+1
                print(f'{name}: {count} original visible/collidable pieces')
            else:
                item.clear()
        stack.pop()
    if len(counts)!=len(SELECT):
        raise RuntimeError('Missing official assets '+str(set(SELECT)-set(counts)))
    output.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(output,encoding='utf-8',xml_declaration=True)
    print('Exported six original, script-free suburban templates',output,output.stat().st_size)
if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('source',type=Path)
    parser.add_argument('output',type=Path)
    a=parser.parse_args()
    generate(a.source,a.output)
