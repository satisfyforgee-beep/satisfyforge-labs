"""Build the self-contained Roblox XML place and a reproducible source package."""
from pathlib import Path
import hashlib
import json
import zipfile
from lxml import etree as E

ROOT=Path(__file__).resolve().parent
DIST=ROOT/'dist'
DIST.mkdir(exist_ok=True)
serial=0
doc=E.Element('roblox',version='4',nsmap={'xmime':'http://www.w3.org/2005/05/xmlmime','xsi':'http://www.w3.org/2001/XMLSchema-instance'})
E.SubElement(doc,'External').text='null'
E.SubElement(doc,'External').text='nil'

def item(parent,cls,name):
    global serial
    serial+=1
    node=E.SubElement(parent,'Item',{'class':cls,'referent':f'RBX{serial:08d}'})
    props=E.SubElement(node,'Properties')
    E.SubElement(props,'string',name='Name').text=name
    return node

def prop(node,kind,name,value):
    p=E.SubElement(node.find('Properties'),kind,name=name)
    p.text=str(value).lower() if isinstance(value,bool) else str(value)
    return p

def vector(node,name,xyz):
    p=E.SubElement(node.find('Properties'),'Vector3',name=name)
    for key,value in zip('XYZ',xyz): E.SubElement(p,key).text=str(value)

def part(parent,name,size,pos,color,cls='Part'):
    node=item(parent,cls,name)
    prop(node,'bool','Anchored',True)
    prop(node,'bool','CanCollide',True)
    prop(node,'token','Material',256)
    prop(node,'token','TopSurface',0); prop(node,'token','BottomSurface',0)
    prop(node,'Color3uint8','Color3uint8',0xff000000|(color[0]<<16)|(color[1]<<8)|color[2])
    vector(node,'size',size)
    cf=E.SubElement(node.find('Properties'),'CoordinateFrame',name='CFrame')
    names=['X','Y','Z','R00','R01','R02','R10','R11','R12','R20','R21','R22']
    for k,v in zip(names,[*pos,1,0,0,0,1,0,0,0,1]): E.SubElement(cf,k).text=str(v)
    if cls=='SpawnLocation': prop(node,'bool','Neutral',True); prop(node,'int','Duration',0)
    return node

workspace=item(doc,'Workspace','Workspace')
prop(workspace,'float','Gravity',196.2)
preview=item(workspace,'Folder','SnackquakeEditorPreview')
part(preview,'Arena',(120,2,115),(0,-1,-16),(23,29,49))
part(preview,'SafeLobby',(120,2,30),(0,0,55),(48,64,83))
part(preview,'PreviewSpawn',(10,1,10),(0,1.5,55),(76,191,255),'SpawnLocation')
part(preview,'RescueChute',(11,5,7),(0,3.5,43),(178,255,96))
for x in [-36,0,36]:
    for z in [-48,-15]:
        part(preview,'BlueRefuge',(16,1,12),(x,8,z),(76,191,255))
        for step in range(1,5): part(preview,'Stair',(12,2*step,4),(x,step,z+18-step*4),(56,95,125))
for row,z in enumerate([22,-24,-63]):
    for col,x in enumerate([-48,-24,0,24,48]):
        part(preview,'CreatureSpot',(6,.18,6),(x,.12,z),(255,102,167) if row==2 else (178,255,96))
for x in [-60,60]: part(preview,'SideRail',(2,5,146),(x,1.5,-1),(76,191,255))
part(preview,'BackRail',(120,5,2),(0,1.5,-74),(255,102,167))
part(preview,'LobbyRail',(120,5,2),(0,1.5,71),(76,191,255))
storage=item(doc,'ReplicatedStorage','ReplicatedStorage')
shared=item(storage,'Folder','SnackquakeShared')
server=item(doc,'ServerScriptService','ServerScriptService')
serverFolder=item(server,'Folder','SnackquakeServer')
starter=item(doc,'StarterPlayer','StarterPlayer')
prop(starter,'float','CharacterWalkSpeed',18)
clientFolder=item(starter,'StarterPlayerScripts','StarterPlayerScripts')
sourceMap={}
def script(parent,cls,name,filename):
    node=item(parent,cls,name)
    source=(ROOT/'src'/filename).read_text()
    p=prop(node,'ProtectedString','Source',''); p.text=E.CDATA(source)
    if cls!='ModuleScript': prop(node,'bool','Disabled',False)
    sourceMap[name]=filename
for name in ['Config','Rules','Creatures']: script(shared,'ModuleScript',name,name+'.lua')
for name in ['World','PlayerData','Analytics']: script(serverFolder,'ModuleScript',name,name+'.lua')
script(serverFolder,'Script','SnackquakeMain','Main.server.lua')
script(serverFolder,'Script','SnackquakeStudioSmoke','StudioSmoke.server.lua')
script(clientFolder,'LocalScript','SnackquakeClient','Client.client.lua')
place=DIST/'Brainrot_Rescue_Snackquake.rbxlx'
E.ElementTree(doc).write(str(place),encoding='utf-8',xml_declaration=True,pretty_print=True)

# Verify XML structure and exact embedded sources; this does not invoke Studio.
parsed=E.parse(str(place))
assert parsed.getroot().get('version')=='4'
refs=[n.get('referent') for n in parsed.findall('.//Item')]
assert len(refs)==len(set(refs))
embedded=[]
for node in parsed.findall('.//Item'):
    if node.get('class') in ['Script','LocalScript','ModuleScript']:
        name=node.find('Properties/string[@name="Name"]').text
        source=node.find('Properties/ProtectedString[@name="Source"]').text
        assert source==(ROOT/'src'/sourceMap[name]).read_text(), name
        embedded.append(name)
assert len(embedded)==9

manifest={'title':'Brainrot Rescue: Snackquake','version':'0.3.0-rescue-rush',
          'engine_tested':False,'published':False,'source_files':{},
          'validation':'Lua-compatible syntax, pure-rule and persistence tests, XML/source integrity only; Roblox Studio runtime evidence is tracked separately'}
for p in sorted((ROOT/'src').glob('*.lua')):
    manifest['source_files'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
manifest['place_sha256']=hashlib.sha256(place.read_bytes()).hexdigest()
(ROOT/'BUILD_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
archive=DIST/'Brainrot_Rescue_Snackquake_Source_Kit.zip'
include=[place,*sorted((ROOT/'src').glob('*.lua')),*sorted((ROOT/'tests').glob('*')),
         ROOT/'build_place.py',ROOT/'BUILD_MANIFEST.json',*sorted(ROOT.glob('*.md'))]
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in include:
        if p.is_file(): z.write(p,p.name if p==place else p.relative_to(ROOT).as_posix())
print(json.dumps({'place':str(place),'archive':str(archive),'embedded_sources':len(embedded),'instances':len(refs),
                  'place_bytes':place.stat().st_size,'archive_bytes':archive.stat().st_size,'engine_tested':False}))
