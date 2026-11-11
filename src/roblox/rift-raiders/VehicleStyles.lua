-- v0.14 Original vehicle geometry kit: visible, separate SUV, pickup,
-- electric crossover, supercar, hypercar and classic-coupe silhouettes.
-- No imported scripts, unlicensed meshes or external texture IDs.
-- Server moves the models with existing verified VehicleSeat controls.
local Styles={}
local variants={
 SUV={length=16,width=8.5,height=6.2,roof=7.4,hood=4.3,
  color=Color3.fromRGB(74,107,116),name="Family SUV",speed=33},
 PICKUP_TRUCK={length=19,width=8.6,height=5.9,roof=6.8,hood=5,
  color=Color3.fromRGB(93,111,130),name="Crew Cab Pickup",speed=35},
 ELECTRIC_CAR={length=16,width=7.9,height=4.5,roof=7.8,hood=4,
  color=Color3.fromRGB(215,220,211),name="Electric Crossover",speed=42},
 SUPERCAR={length=17,width=8.1,height=3.4,roof=5.8,hood=5.8,
  color=Color3.fromRGB(194,43,44),name="Low Sports Coupe",speed=57},
 HYPERCAR={length=18,width=8.6,height=3,roof=6.2,hood=6.4,
  color=Color3.fromRGB(52,66,86),name="Carbon Hypercar",speed=63},
 CLASSIC_CAR={length=18,width=8.1,height=4.7,roof=6,hood=6.1,
  color=Color3.fromRGB(164,114,75),name="Vintage Coupe",speed=35},
}
Styles.Variants=variants
local function obj(m,name,sz,at,mat,color,shape)
 local p=Instance.new(shape or "Part")
 p.Name=name;p.Anchored=true;p.CanCollide=false;p.CanTouch=false
 p.CanQuery=false;p.Size=sz;p.CFrame=at
 p.Material=mat or Enum.Material.Metal
 p.Color=color or Color3.fromRGB(136,145,150)
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=m
 return p
end
local function addRotatedCylinder(m,name,cf,pos,diam,thickness,color)
 return obj(m,name,Vector3.new(diam,thickness,diam),
  cf*CFrame.new(pos)*CFrame.Angles(0,0,math.rad(90)),
  Enum.Material.SmoothPlastic,color)
end
local function wheel(m,cf,x,z,radius,offset)
 local black=Color3.fromRGB(32,34,37)
 local hub=Color3.fromRGB(178,184,190)
 local tire=obj(m,"Detailed Radial Tire",Vector3.new(radius*2,.9,radius*2),
  cf*CFrame.new(x,-1.1,z)*CFrame.Angles(0,0,math.pi*.5),
  Enum.Material.Rubber,black,"Part")
 tire.Shape=Enum.PartType.Cylinder
 local disc=obj(m,"Alloy Wheel Hub",Vector3.new(radius*1.33,1,radius*1.33),
  cf*CFrame.new(x+(x>0 and .25 or -.25),-1.1,z)*
   CFrame.Angles(0,0,math.pi*.5),
  Enum.Material.Metal,hub)
 disc.Shape=Enum.PartType.Cylinder
 for k=1,5 do
  local a=math.pi*2*k/5
  obj(m,"Forged Alloy Wheel Spoke",Vector3.new(.18,.55,.18),
   cf*CFrame.new(x+(x>0 and .84 or -.84),
    -1.1+math.sin(a)*radius*.42,z+math.cos(a)*radius*.42),
   Enum.Material.Metal,Color3.fromRGB(111,133,145))
 end
 return tire
end
local function panel(m,name,sz,cf,color,material)
 return obj(m,name,sz,cf,material or Enum.Material.SmoothPlastic,color)
end
local function wedge(m,name,sz,cf,color)
 return obj(m,name,sz,cf,Enum.Material.SmoothPlastic,color,"WedgePart")
end
local function body(m,cf,t)
 local L,W=t.length,t.width
 local hoodL=t.hood
 local roofL=t.roof
 local isPickup=t==variants.PICKUP_TRUCK
 local sport=t==variants.SUPERCAR or t==variants.HYPERCAR
 local isClassic=t==variants.CLASSIC_CAR
 local isElectric=t==variants.ELECTRIC_CAR
 local isSUV=t==variants.SUV
 local paint=t.color
 local dark=Color3.fromRGB(52,58,64)
 local glass=Color3.fromRGB(67,102,126)
 local lights=Color3.fromRGB(236,239,221)
 local tail=Color3.fromRGB(202,51,49)
 -- Flat steel lower frame, sloped real wheel arches, chrome/black trim.
 panel(m,"Monocoque Safety Chassis",Vector3.new(W,1.5,L*.93),
  cf*CFrame.new(0,0,0),Color3.fromRGB(82,87,88),Enum.Material.Metal)
 panel(m,"Sculpted Door Panels",Vector3.new(W-.2,1.3,L*.72),
  cf*CFrame.new(0,.9,0),paint)
 panel(m,"Long Hood Shell",Vector3.new(W*.94,.8,L*.26),
  cf*CFrame.new(0,1.12,-L*.345),paint)
 panel(m,"Rounded Rear Body",Vector3.new(W*.92,1,L*.25),
  cf*CFrame.new(0,1.1,L*.34),paint)
 -- Multi-part roof, windscreen, rear screen; cockpit is not just a cube.
 local roofHeight=t.height*.49+1
 local roofZ=isPickup and -L*.08 or sport and .16 or 0
 local upperWidth=W*(sport and .64 or .72)
 if isPickup then
  roofHeight=3.55
  roofZ=-L*.13
 elseif isSUV then
  roofHeight=4.1
 end
 local capLength=isPickup and L*.35 or isSUV and L*.58 or
  sport and L*.36 or L*.46
 panel(m,"Vehicle Roof Profile",Vector3.new(upperWidth,.25,capLength),
  cf*CFrame.new(0,roofHeight,roofZ),paint)
 wedge(m,"Front Slanted Windshield",Vector3.new(upperWidth,roofHeight*.48,2.3),
  cf*CFrame.new(0,roofHeight*.74,roofZ-capLength*.5-.3)*
   CFrame.Angles(0,math.pi,0),
  glass)
 wedge(m,"Rear Slanted Glass",Vector3.new(upperWidth,roofHeight*.45,2),
  cf*CFrame.new(0,roofHeight*.74,roofZ+capLength*.5+.3),
  glass)
 for _,side in ipairs({-1,1}) do
  local sx=side*upperWidth*.5
  local sideLength=capLength*.55
  local panelX=sx+(side>0 and .02 or -.02)
  local w=panel(m,"Side Window Dark Tint",Vector3.new(.09,roofHeight*.47,sideLength),
   cf*CFrame.new(panelX,roofHeight*.77,roofZ),
   glass,Enum.Material.Glass)
  w.Transparency=.18
  panel(m,"Recessed Side Door Trim",Vector3.new(.12,.1,L*.28),
   cf*CFrame.new(side*(W*.5+.09),1.15,0),
   dark,Enum.Material.Metal)
  panel(m,"Side Mirror Assembly",Vector3.new(.9,.45,.72),
   cf*CFrame.new(side*(W*.5+.5),2.15,-L*.13),
   dark,Enum.Material.Metal)
  panel(m,"Side Door Handle",Vector3.new(.18,.2,1),
   cf*CFrame.new(side*(W*.5+.16),1.88,L*.03),
   Color3.fromRGB(179,184,184),Enum.Material.Metal)
  for _,z in ipairs({-L*.32,L*.32}) do
   wheel(m,cf,side*(W*.5-.05),z,(isSUV or isPickup) and 1.9 or sport and 1.65 or 1.7)
   panel(m,"Wheel Arch Accent",Vector3.new(.18,.22,4.0),
    cf*CFrame.new(side*W*.5,.7,z),
    Color3.fromRGB(46,48,52),Enum.Material.Metal)
  end
  panel(m,"LED Headlight",Vector3.new(W*.18,.42,.2),
   cf*CFrame.new(side*W*.29,1.3,-L*.5+.18),
   lights,Enum.Material.Neon)
  panel(m,"Rear Tail Lamp",Vector3.new(W*.19,.45,.15),
   cf*CFrame.new(side*W*.3,1.38,L*.5-.18),
   tail,Enum.Material.Neon)
 end
 panel(m,"Front Brake Cooling Grille",Vector3.new(W*.64,.5,.16),
  cf*CFrame.new(0,.6,-L*.49),
  dark,Enum.Material.Metal)
 panel(m,"Tail Exhaust Panel",Vector3.new(W*.58,.3,.16),
  cf*CFrame.new(0,.5,L*.49),
  dark,Enum.Material.Metal)
 if isPickup then
  -- Actual visibly separate truck bed, inner trough and tailgate.
  local start=L*.17
  for _,side in ipairs({-1,1}) do
   panel(m,"Pickup Bed Side Wall",Vector3.new(.7,1.8,L*.37),
    cf*CFrame.new(side*(W*.5-.25),1.65,start+L*.08),paint)
  end
  panel(m,"Pickup Cargo Bed",Vector3.new(W-1,.25,L*.37),
   cf*CFrame.new(0,.78,start+L*.08),
   Color3.fromRGB(80,85,91),Enum.Material.Metal)
  panel(m,"Pickup Tailgate",Vector3.new(W,1.7,.38),
   cf*CFrame.new(0,1.65,L*.46),paint)
  for k=1,8 do
   panel(m,"Truck Bed Ridged Liner",Vector3.new(W-.95,.1,.1),
    cf*CFrame.new(0,1,start+L*.08-L*.16+k*L*.038),
    Color3.fromRGB(112,118,121),Enum.Material.Metal)
  end
 elseif sport then
  -- Extreme low nose and rear aero wing; hypercar has double wing and fins.
  wedge(m,"Wedge Front Aero Nose",Vector3.new(W*.94,1.3,L*.26),
   cf*CFrame.new(0,.4,-L*.37),paint)
  panel(m,"Front Carbon Lip",Vector3.new(W*.97,.2,1.2),
   cf*CFrame.new(0,-.15,-L*.48),
   Color3.fromRGB(33,36,41),Enum.Material.Metal)
  for _,side in ipairs({-1,1}) do
   panel(m,"Rear Aero Wing Support",Vector3.new(.25,1.5,.4),
    cf*CFrame.new(side*W*.28,2.2,L*.38),
    Color3.fromRGB(45,52,62),Enum.Material.Metal)
  end
  panel(m,"Rear Downforce Wing",Vector3.new(W*.9,.28,1.6),
   cf*CFrame.new(0,3.15,L*.39),dark,Enum.Material.Metal)
  if t==variants.HYPERCAR then
   for _,side in ipairs({-1,1}) do
    wedge(m,"Carbon Aero Dorsal Fin",Vector3.new(.55,1.6,3.8),
     cf*CFrame.new(side*W*.34,2.1,L*.06),
     Color3.fromRGB(46,55,62))
   end
   panel(m,"Hypercar Engine Glass",Vector3.new(W*.6,.16,2.5),
    cf*CFrame.new(0,2.08,L*.22),glass,Enum.Material.Glass).Transparency=.28
  end
 elseif isSUV then
  for _,side in ipairs({-1,1}) do
   panel(m,"SUV Rooftop Rack",Vector3.new(.21,.18,L*.53),
    cf*CFrame.new(side*W*.27,roofHeight+.24,0),
    Color3.fromRGB(49,59,66),Enum.Material.Metal)
  end
  panel(m,"Rear Hatch With Spare",Vector3.new(W*.36,1.5,.2),
   cf*CFrame.new(0,1.7,L*.48),dark,Enum.Material.Rubber)
 elseif isElectric then
  for _,side in ipairs({-1,1}) do
   panel(m,"Electric Neon Trim",Vector3.new(.18,.17,L*.32),
    cf*CFrame.new(side*(W*.5+.02),.65,0),
    Color3.fromRGB(57,174,185),Enum.Material.Neon)
  end
  panel(m,"EV Charge Flap",Vector3.new(.14,.7,.9),
   cf*CFrame.new(W*.5+.09,1.5,L*.24),
   Color3.fromRGB(75,159,170),Enum.Material.Metal)
 elseif isClassic then
  panel(m,"Chrome Classic Front Bumper",Vector3.new(W,.35,.8),
   cf*CFrame.new(0,.6,-L*.5),Color3.fromRGB(208,206,193),Enum.Material.Metal)
  panel(m,"Vintage Tail Chrome",Vector3.new(W,.35,.8),
   cf*CFrame.new(0,.6,L*.5),Color3.fromRGB(208,206,193),Enum.Material.Metal)
  panel(m,"Classic Long Bonnet Trim",Vector3.new(.18,.18,L*.22),
   cf*CFrame.new(0,1.57,-L*.28),Color3.fromRGB(213,203,173),Enum.Material.Metal)
 end
end
function Styles.Build(parent,cf,id)
 local tier=variants[id]
 if not tier then return nil end
 local model=Instance.new("Model")
 model.Name="Detailed Custom "..id
 model:SetAttribute("Silhouette",tier.name)
 model:SetAttribute("OriginalGeometry",true)
 model.Parent=parent
 body(model,cf,tier)
 model:SetAttribute("MeshStyle","Original modular vehicle geometry")
 return model
end
return Styles
