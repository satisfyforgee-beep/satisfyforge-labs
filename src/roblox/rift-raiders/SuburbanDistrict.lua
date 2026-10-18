-- v0.14 Script-free official Roblox Studio Suburban template architecture.
-- Detailed source houses/stores remain actual prefabs, not generated cubes.
local ServerStorage=game:GetService("ServerStorage")
local Suburbs={}
local arrivals=Vector3.new(0,8,3425)
local layout={
 {name="Suburban Single Story House",center=Vector3.new(-200,0,3530)},
 {name="Suburban Two Story House",center=Vector3.new(-25,0,3565)},
 {name="Suburban Convenience Market",center=Vector3.new(215,0,3490)},
 {name="Suburban Gas Station",center=Vector3.new(220,0,3650)},
 {name="Suburban Detailed Garage",center=Vector3.new(25,0,3710)},
 {name="Suburban Playground",center=Vector3.new(-200,0,3710)},
}
local function solid(parent,name,size,pos,color,mat,collision)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=CFrame.new(pos)
 p.Anchored=true;p.CanCollide=collision~=false;p.CanTouch=false
 p.Material=mat or Enum.Material.Concrete;p.Color=color
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=parent
 return p
end
local function sign(folder,title,position)
 local post=solid(folder,title.." Signboard",Vector3.new(17,5,.4),
  position,Color3.fromRGB(69,81,95),Enum.Material.Metal,false)
 local gui=Instance.new("SurfaceGui")
 gui.Face=Enum.NormalId.Front;gui.CanvasSize=Vector2.new(420,130)
 gui.PixelsPerStud=30;gui.Parent=post
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1)
 label.Text=title;label.TextScaled=true;label.TextWrapped=true
 label.Font=Enum.Font.GothamBold
 label.TextColor3=Color3.fromRGB(240,233,209)
 label.BackgroundTransparency=1;label.Parent=gui
 return post
end
function Suburbs.Build(world)
 local source=ServerStorage:WaitForChild("OfficialSuburbanArchitecture")
 local folder=Instance.new("Folder")
 folder.Name="Official Detailed Suburban Town";folder.Parent=world
 local terrain=workspace.Terrain
 terrain:FillBlock(CFrame.new(0,-6,3600),
  Vector3.new(760,13,510),Enum.Material.Grass)
 for _,z in ipairs({3435,3610}) do
  solid(folder,"Neighborhood Asphalt Boulevard",
   Vector3.new(730,.65,22),Vector3.new(0,1.05,z),
   Color3.fromRGB(73,76,79),Enum.Material.Asphalt,true)
  for x=-342,342,38 do
   solid(folder,"Road Center Lane Paint",
    Vector3.new(14,.1,.4),Vector3.new(x,1.42,z),
    Color3.fromRGB(223,207,149),Enum.Material.Concrete,false)
  end
 end
 for _,x in ipairs({-315,80}) do
  solid(folder,"Suburban Cross Avenue",
   Vector3.new(17,.7,310),Vector3.new(x,1,3570),
   Color3.fromRGB(75,79,83),Enum.Material.Asphalt,true)
 end
 local imported=0
 local countParts=0
 for _,asset in ipairs(layout) do
  local sample=source:FindFirstChild(asset.name)
  if not sample then warn("Missing official suburban prefab",asset.name) continue end
  local clone=sample:Clone()
  -- Roblox's Playground template is a Folder containing many 3D models.
  -- Wrap it into a Model so it supports precise bounding-box relocation.
  if not clone:IsA("Model") then
   local wrapper=Instance.new("Model")
   wrapper.Name=clone.Name
   for _,child in ipairs(clone:GetChildren()) do
    child.Parent=wrapper
   end
   clone:Destroy()
   clone=wrapper
  end
  clone.Parent=folder
  local box,sz=clone:GetBoundingBox()
  local offset=Vector3.new(asset.center.X-box.Position.X,
   2.05-(box.Position.Y-sz.Y*.5),
   asset.center.Z-box.Position.Z)
  clone:PivotTo(clone:GetPivot()+offset)
  local pieces=0
  for _,node in ipairs(clone:GetDescendants()) do
   if node:IsA("LuaSourceContainer") then
    node:Destroy()
   elseif node:IsA("BasePart") then
    node.Anchored=true
    node.CanTouch=false
    pieces+=1
   end
  end
  clone:SetAttribute("OfficialTemplate",true)
  clone:SetAttribute("OriginalVisiblePieces",pieces)
  clone:SetAttribute("EnvironmentalPrefab",true)
  imported+=1;countParts+=pieces
 end
 local arrival=solid(folder,"Suburban Community Arrival",
  Vector3.new(20,.5,15),Vector3.new(0,1.65,3425),
  Color3.fromRGB(154,153,144),Enum.Material.Concrete,true)
 sign(folder,"RIFTLIFE SUBURBAN DISTRICT",Vector3.new(0,11,3407))
 sign(folder,"SHOPS • GAS STATION • HOMES",
  Vector3.new(15,8,3461))
 folder:SetAttribute("OfficialPrefabCount",imported)
 folder:SetAttribute("DetailedSourceParts",countParts)
 folder:SetAttribute("GeometryOrigin","Official Roblox Studio Suburban")
 folder:SetAttribute("EnvironmentOnly",true)
 return arrivals
end
return Suburbs
