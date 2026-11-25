-- v0.17: replayable hidden-keepsake exploration loop in official Suburbia.
-- Collectible actions are allowed only from nearby live world prompts.
local Players=game:GetService("Players")
local Discovery={}
local sites={
 {"Lost Camera Lens",Vector3.new(-204,4.2,3507),Color3.fromRGB(117,198,222)},
 {"Family Heirloom Key",Vector3.new(-14,4.2,3539),Color3.fromRGB(243,207,105)},
 {"Market Shopping Token",Vector3.new(192,4.2,3469),Color3.fromRGB(156,211,127)},
 {"Vintage Fuel Badge",Vector3.new(226,4.2,3630),Color3.fromRGB(225,154,101)},
 {"Collector Gear",Vector3.new(25,4.2,3701),Color3.fromRGB(171,185,203)},
 {"Playground Lucky Charm",Vector3.new(-199,4.2,3685),Color3.fromRGB(216,146,209)},
 {"Bridge Map Fragment",Vector3.new(-91,4.2,3608),Color3.fromRGB(114,172,216)},
 {"Suburban Explorer Star",Vector3.new(60,4.2,3439),Color3.fromRGB(238,221,113)},
}
Discovery.Sites=sites
local context
local folder
local function dayKey()
 local t=os.date("!*t")
 return t.year*10000+t.month*100+t.day
end
function Discovery.Normalize(value)
 value=type(value)=="table" and value or {}
 local result={day=dayKey(),found={}}
 if value.day==result.day and type(value.found)=="table" then
  for i=1,#sites do
   if value.found[i]==true then result.found[i]=true end
  end
 end
 return result
end
function Discovery.Count(s)
 local count=0
 for i=1,#sites do
  if s and s.found and s.found[i]==true then count+=1 end
 end
 return count
end
local function refresh(p)
 local state=context and context.getProfile(p)
 local s=state and state.discover
 if not s then return end
 if s.day~=dayKey() then
  s.day=dayKey();s.found={}
 end
 p:SetAttribute("RRDiscoverCount",Discovery.Count(s))
 p:SetAttribute("RRDiscoverTotal",#sites)
 p:SetAttribute("RRDiscoverDay",s.day)
end
function Discovery.Sync(p)
 if context then refresh(p) end
end
function Discovery.Collect(p,index)
 if not context or type(index)~="number" or
  index%1~=0 or not sites[index] then return false end
 local root=p.Character and p.Character:FindFirstChild("HumanoidRootPart")
 local char=p.Character
 local hum=char and char:FindFirstChildOfClass("Humanoid")
 local location=sites[index][2]
 if not root or not hum or hum.Health<=0 or
  (root.Position-location).Magnitude>13.5 then return false end
 local profile=context.getProfile(p)
 if not profile or not profile.discover then return false end
 local record=profile.discover
 if record.day~=dayKey() then record.day=dayKey();record.found={} end
 if record.found[index] then
  context.tell(p,"YOU ALREADY FOUND THIS KEEPSAKE TODAY. EXPLORE FOR MORE!")
  return false
 end
 record.found[index]=true
 local total=Discovery.Count(record)
 local value=18+index*2
 context.reward(p,value,10,0)
 context.tell(p,"DISCOVERED: "..sites[index][1]:upper().."! +"..value..
  " COINS • "..total.."/"..#sites.." KEEPSAKES.")
 if total==#sites then
  context.reward(p,180,45,0)
  context.tell(p,"SUBURBAN EXPLORER COMPLETE! +180 BONUS COINS."..
   " THE COLLECTION RETURNS TOMORROW!")
 end
 refresh(p)
 return true
end
local function physicalToken(parent,index,label,pos,color)
 local anchor=Instance.new("Part")
 anchor.Name="Hidden Keepsake "..index
 anchor.Size=Vector3.new(2.2,2.2,2.2)
 anchor.Shape=Enum.PartType.Ball
 anchor.CFrame=CFrame.new(pos)
 anchor.Anchored=true;anchor.CanCollide=false
 anchor.CanQuery=false;anchor.CanTouch=false
 anchor.Material=Enum.Material.Glass;anchor.Transparency=.24
 anchor.Color=color;anchor.CastShadow=false
 anchor.Parent=parent
 local mesh=Instance.new("SpecialMesh")
 mesh.MeshType=Enum.MeshType.Sphere
 mesh.Scale=Vector3.new(1,.72,1)
 mesh.Parent=anchor
 local ring=Instance.new("SelectionBox")
 ring.Adornee=anchor
 ring.SurfaceTransparency=.72
 ring.Color3=color;ring.LineThickness=.05
 ring.Parent=anchor
 local light=Instance.new("PointLight")
 light.Color=color;light.Brightness=1.2;light.Range=9
 light.Shadows=false;light.Parent=anchor
 local billboard=Instance.new("BillboardGui")
 billboard.Name="Keepsake Discovery Billboard"
 billboard.Size=UDim2.fromOffset(175,40)
 billboard.StudsOffsetWorldSpace=Vector3.new(0,2.3,0)
 billboard.MaxDistance=36;billboard.AlwaysOnTop=false
 billboard.Parent=anchor
 local title=Instance.new("TextLabel")
 title.Size=UDim2.fromScale(1,1)
 title.BackgroundTransparency=.32
 title.BackgroundColor3=Color3.fromRGB(37,52,62)
 title.TextColor3=Color3.fromRGB(246,235,198)
 title.Font=Enum.Font.GothamBold
 title.TextScaled=true
 title.Text="DISCOVER • "..index.."/"..#sites
 title.Parent=billboard
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="Discover Keepsake Prompt"
 prompt.ActionText="COLLECT KEEPSAKE"
 prompt.ObjectText=label
 prompt.MaxActivationDistance=11
 prompt.HoldDuration=.45
 prompt.RequiresLineOfSight=false
 prompt.Parent=anchor
 prompt.Triggered:Connect(function(p)
  Discovery.Collect(p,index)
 end)
 anchor:SetAttribute("DiscoverIndex",index)
 return anchor
end
function Discovery.Build(world,options)
 context=options
 if folder then folder:Destroy() end
 folder=Instance.new("Folder")
 folder.Name="Suburban Discovery Trail"
 folder.Parent=world
 for index,entry in ipairs(sites) do
  physicalToken(folder,index,entry[1],entry[2],entry[3])
 end
 folder:SetAttribute("CollectibleCount",#sites)
 folder:SetAttribute("DailyReset","UTC")
 folder:SetAttribute("OwnershipValidatedByServer",true)
 return folder
end
return Discovery
