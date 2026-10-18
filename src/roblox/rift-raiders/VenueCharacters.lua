-- Stylized, script-free workplace NPCs. Deliberately cheap to render:
-- no Roblox avatar fetches, external asset IDs, per-frame loops, or physics.
local VenueCharacters={}
local function block(parent,name,size,cf,color,material,shape)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf;p.Color=color
 p.Material=material or Enum.Material.SmoothPlastic
 if shape then p.Shape=shape end
 p.Anchored=true;p.CanCollide=false;p.CanTouch=false;p.CanQuery=false
 p.TopSurface=Enum.SurfaceType.Smooth;p.BottomSurface=Enum.SurfaceType.Smooth
 p.Parent=parent
 return p
end
function VenueCharacters.Create(parent,id,ground,name,shirt,dialogue)
 -- Workplace coordinates were near the floor *center*, so NPC shoe soles
 -- were visibly hovering about .4 studs above the real indoor surfaces.
 ground=ground*CFrame.new(0,-.38,0)
 local rig=Instance.new("Model")
 rig.Name=id;rig:SetAttribute("NPCType","StaticWorkplaceGuide")
 rig:SetAttribute("ResidentName",name)
 rig.Parent=parent
 local pivot=block(rig,"Guide Root",Vector3.new(.2,.2,.2),
  ground*CFrame.new(0,.2,0),Color3.fromRGB(255,255,255))
 pivot.Transparency=1;rig.PrimaryPart=pivot
 local skin=Color3.fromRGB(195,142,111)
 local denim=Color3.fromRGB(47,57,79)
 block(rig,"Torso Uniform",Vector3.new(1.7,2.05,.85),
  ground*CFrame.new(0,3.1,0),shirt)
 block(rig,"Head",Vector3.new(1.25,1.25,1.25),
  ground*CFrame.new(0,4.8,0),skin,nil,Enum.PartType.Ball)
 block(rig,"Short Hair",Vector3.new(1.32,.4,1.3),
  ground*CFrame.new(0,5.27,0),Color3.fromRGB(46,39,37))
 for _,side in ipairs({-1,1}) do
  block(rig,side==-1 and "Left Sleeve" or "Right Sleeve",
   Vector3.new(.55,1.55,.7),
   ground*CFrame.new(side*1.13,3.12,0),shirt)
  block(rig,side==-1 and "Left Hand" or "Right Hand",
   Vector3.new(.51,.6,.6),
   ground*CFrame.new(side*1.13,2.04,0),skin)
  block(rig,side==-1 and "Left Pants" or "Right Pants",
   Vector3.new(.73,1.7,.85),
   ground*CFrame.new(side*.46,1.37,0),denim)
  block(rig,side==-1 and "Left Shoe" or "Right Shoe",
   Vector3.new(.75,.37,1.1),
   ground*CFrame.new(side*.46,.35,-.13),Color3.fromRGB(37,41,44))
 end
 local badge=block(rig,"Name Badge",Vector3.new(.65,.3,.08),
  ground*CFrame.new(.48,3.55,-.47),Color3.fromRGB(246,211,127),
  Enum.Material.Metal)
 local gui=Instance.new("BillboardGui")
 gui.Name="Local Character Name";gui.Size=UDim2.fromOffset(180,51)
 gui.StudsOffsetWorldSpace=Vector3.new(0,5.5,0)
 gui.MaxDistance=52;gui.Parent=pivot
 local title=Instance.new("TextLabel")
 title.Size=UDim2.fromScale(1,1);title.TextWrapped=true
 title.BackgroundTransparency=.12
 title.BackgroundColor3=Color3.fromRGB(34,47,62)
 title.TextColor3=Color3.fromRGB(246,233,200)
 title.TextSize=13;title.Font=Enum.Font.GothamBold
 title.Text=name.."\nASK FOR DIRECTIONS";title.Parent=gui
 local prompt=Instance.new("ProximityPrompt")
 prompt.Name="Talk to "..name
 prompt.ObjectText=name;prompt.ActionText="ASK FOR HELP"
 prompt.HoldDuration=.35;prompt.MaxActivationDistance=7
 prompt.RequiresLineOfSight=false;prompt.Parent=pivot
 prompt.Triggered:Connect(function(player)
  local character=player.Character
  local root=character and character:FindFirstChild("HumanoidRootPart")
  local human=character and character:FindFirstChildOfClass("Humanoid")
  if root and human and human.Health>0 and
   (root.Position-pivot.Position).Magnitude<=8 and
   type(dialogue)=="function" then
   dialogue(player)
  end
 end)
 return rig
end
return VenueCharacters
