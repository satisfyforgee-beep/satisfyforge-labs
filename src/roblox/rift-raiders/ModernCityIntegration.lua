-- Official Roblox Modern City district integration.
-- Imported geometry and material variants originate from Roblox Studio's
-- built-in Modern City template. All imported executable scripts were removed.
-- World construction remains separate so this art can be reused in future games.
local Integration={}
local ORIGIN=Vector3.new(720,0,200)
local DESTINATION=Vector3.new(0,0,2350)
local DELTA=DESTINATION-ORIGIN

local function anchor(parent,name,size,position,color,material,collidable)
 local p=Instance.new("Part")
 p.Name=name; p.Anchored=true; p.CanCollide=collidable==true
 p.CanTouch=false; p.CanQuery=true
 p.Size=size; p.Position=position
 p.Material=material or Enum.Material.Metal
 p.Color=color or Color3.fromRGB(64,85,99)
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
local function board(parent,name,position,title,subtitle)
 local base=anchor(parent,name,Vector3.new(13,8,.8),position,
  Color3.fromRGB(33,47,62),Enum.Material.Metal,true)
 local face=Instance.new("SurfaceGui")
 face.Name="City Wayfinding Sign"
 face.Face=Enum.NormalId.Front
 face.CanvasSize=Vector2.new(850,520)
 face.LightInfluence=.25; face.Parent=base
 local main=Instance.new("TextLabel")
 main.BackgroundTransparency=1
 main.Size=UDim2.new(.94,0,.6,0)
 main.Position=UDim2.new(.03,0,.04,0)
 main.Text=title; main.TextWrapped=true
 main.Font=Enum.Font.GothamBold; main.TextScaled=true
 main.TextColor3=Color3.fromRGB(248,238,211); main.Parent=face
 local sub=Instance.new("TextLabel")
 sub.BackgroundTransparency=1
 sub.Size=UDim2.new(.94,0,.28,0)
 sub.Position=UDim2.new(.03,0,.65,0)
 sub.Text=subtitle; sub.TextWrapped=true
 sub.Font=Enum.Font.Gotham; sub.TextScaled=true
 sub.TextColor3=Color3.fromRGB(142,206,227); sub.Parent=face
 return base
end
local function portal(parent,position,title,description,callback)
 local base=board(parent,"Modern City Wayfinding Terminal",position,title,description)
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="Travel to "..title
 prompt.ActionText="TRAVEL"
 prompt.ObjectText=title
 prompt.HoldDuration=.3
 prompt.MaxActivationDistance=14
 prompt.RequiresLineOfSight=false
 prompt.Parent=base
 prompt.Triggered:Connect(callback)
 return base
end
function Integration.Build(world,spawn,tell)
 local imported=workspace:FindFirstChild("OfficialModernCityDistrict")
 if not imported or not imported:IsA("Model") then
  warn("Official Modern City art not loaded; leaving original hub spawn")
  return nil
 end
 -- The source art is a prebuilt street block around x=720,z=200. Move it
 -- to a new streaming-friendly region, keeping the original street layout.
 imported:PivotTo(imported:GetPivot()+DELTA)
 imported:SetAttribute("ArtSource","Official Roblox Studio Modern City Template")
 imported:SetAttribute("ImportedScriptsRemoved",true)
 imported:SetAttribute("OriginalCenter","720,0,200")
 imported:SetAttribute("WorldRegion","DOWNTOWN")
 imported.Name="OfficialModernCityDistrict"
 local folder=Instance.new("Folder")
 folder.Name="Downtown Wayfinding"
 folder.Parent=world
 -- The extracted city Model already contains its static asphalt foundation,
 -- so both edit mode and Play mode show buildings grounded in a real street.
 local pad=anchor(folder,"Downtown Arrival Sidewalk",Vector3.new(13,.35,11),
  Vector3.new(0,.68,2215),Color3.fromRGB(67,70,72),
  Enum.Material.Asphalt,true)
 -- Paint a recognizable pedestrian crossing at the welcome plaza.
 for i=-4,4 do
  anchor(folder,"Downtown Arrival Crosswalk",Vector3.new(2.5,.1,9),
   Vector3.new(i*3.8,.12,2196),
   Color3.fromRGB(233,230,215),Enum.Material.Concrete,false)
 end
 pad.Transparency=.12
 -- The city becomes the player's first impression, instead of the block arena.
 if spawn then
  spawn.CFrame=CFrame.new(0,1.5,2215)*CFrame.Angles(0,math.pi,0)
  spawn.Size=Vector3.new(9,1,9)
  spawn.Material=Enum.Material.Concrete
  spawn.Color=Color3.fromRGB(148,155,159)
  spawn.Transparency=1
  spawn.CanCollide=false
 end
 portal(folder,Vector3.new(23,7,2215),
  "LIFE CITY JOBS", "60 CAREERS • STORES • HOMES",function(player)
   if player.Character then
    player.Character:PivotTo(CFrame.new(0,7,1600))
    tell(player,"WELCOME TO LIFE CITY • START YOUR CAREER!")
   end
  end)
 portal(folder,Vector3.new(-23,7,2215),
  "RIFT ADVENTURES","PORTALS • SPORTS • CASTLES",function(player)
   if player.Character then
    player.Character:PivotTo(CFrame.new(0,6,0))
    tell(player,"RIFT ADVENTURES • ENTER THE HUB!")
   end
  end)
 portal(folder,Vector3.new(0,7,1675),
  "MODERN DOWNTOWN","REAL 3D CITY • SHOPS • STREETS",function(player)
   if player.Character then
    player.Character:PivotTo(CFrame.new(0,8,2215))
    tell(player,"WELCOME TO MODERN DOWNTOWN!")
   end
  end)
 -- Street traffic and shop props are decorative; never claim drivable assets
 -- are actually usable unless server-owned physics controls are implemented.
 return Vector3.new(0,8,2215)
end
return Integration
