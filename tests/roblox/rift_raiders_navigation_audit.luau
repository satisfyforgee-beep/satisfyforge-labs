local RunService=game:GetService("RunService")
RunService:Run()
task.wait(3)
-- v0.28 navigation reconnaissance. Read-only on the running world.
local world=workspace:WaitForChild("RiftRaidersWorld",30)
local arch=world:WaitForChild("Official Detailed Suburban Town",30)
local PathfindingService=game:GetService("PathfindingService")
local size=Vector3.new(2.3,5,2.3)
local count=0
local function scan(point,building)
 local overlaps=workspace:GetPartBoundsInBox(CFrame.new(point),size)
 local blockers={}
 for _,part in ipairs(overlaps) do
  if part.CanCollide and part:IsDescendantOf(building) and
   part.Size.Y>.65 then
   table.insert(blockers,part.Name)
  end
 end
 local rp=RaycastParams.new()
 rp.FilterType=Enum.RaycastFilterType.Include
 rp.FilterDescendantsInstances={building,workspace.Terrain}
 local result=workspace:Raycast(point+Vector3.new(0,12,0),Vector3.new(0,-25,0),rp)
 return #blockers,result and result.Position.Y or -999,table.concat(blockers,","):sub(1,80)
end
for _,marker in ipairs(arch:GetDescendants()) do
 if marker:IsA("BasePart") and marker:GetAttribute("DoorAccessKey") then
  count+=1
  local key=marker:GetAttribute("DoorAccessKey")
  local building=marker.Parent
  local pos=marker.Position
  if key=="HOUSE_ONE" or key=="HOUSE_TWO" then
   assert(math.abs(pos.Y-6.1)<.35,
    "original suburban front door is floating high above ground: "..
     key.." actual="..pos.Y)
  end
  local bbox,bsize=building:GetBoundingBox()
  print("NAV_DOOR",key,"marker",pos,"build_center",bbox.Position,"buildingSize",bsize)
  for _,axis in ipairs({Vector3.new(1,0,0),Vector3.new(0,0,1)}) do
   for _,s in ipairs({-1,1}) do
    local offset=axis*s*5
    local pt=pos+offset
    local n,fy,names=scan(pt,building)
    print("NAV_SIDE",key,(axis.X==1 and "X" or "Z")..(s==1 and "+" or "-"),
     "B",n,"floorHeight",fy,"blockers",names)
   end
  end
 end
end
assert(count==6,"missing original suburban door controller")
print("NAV_AUDIT_DOORS",count)
print("SF_RIFT_SMOKE_PASS")
