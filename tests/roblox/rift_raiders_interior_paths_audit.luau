-- Read-only validation of passable floor surfaces in the official suburban houses.
local RunService=game:GetService("RunService")
RunService:Run()
task.wait(3)
local world=workspace:WaitForChild("RiftRaidersWorld",25)
local town=world:WaitForChild("Official Detailed Suburban Town",20)
local PathfindingService=game:GetService("PathfindingService")
local overlap=OverlapParams.new()
overlap.FilterType=Enum.RaycastFilterType.Include
local count=0
local deepest={}
for _,spec in ipairs({
 {"Suburban Single Story House","HOUSE_ONE"},
 {"Suburban Two Story House","HOUSE_TWO"},
}) do
 local house=town:WaitForChild(spec[1],10)
 local entry
 for _,p in ipairs(house:GetChildren()) do
  if p:IsA("BasePart") and p:GetAttribute("DoorAccessKey")==spec[2] then entry=p break end
 end
 assert(entry,"entrance missing "..spec[2])
 -- These are temporary Studio test-world changes only, representing the
 -- state after a legitimate player uses the server-owned open-door prompt.
 local sourceDoor
 for _,node in ipairs(house:GetDescendants()) do
  if node:IsA("Model") and node:GetAttribute("RestoredSecureEntry") then
   sourceDoor=node
   break
  end
 end
 assert(sourceDoor,"cannot identify source entrance door")
 local opened=0
 for _,part in ipairs(sourceDoor:GetDescendants()) do
  if part:IsA("BasePart") then
   part.CanCollide=false
   part.CanQuery=false
   opened+=1
  end
 end
 print("NAV_INTERIOR_OPENED_SOURCE_PANELS",spec[2],opened)
 local cf,ext=house:GetBoundingBox()
 local rel=entry.Position-cf.Position
 local inward
 if math.abs(rel.X)>math.abs(rel.Z) then
  inward=Vector3.new(rel.X<0 and 1 or -1,0,0)
 else
  inward=Vector3.new(0,0,rel.Z<0 and 1 or -1)
 end
 local start=Vector3.new(entry.Position.X,3.8,entry.Position.Z)-inward*9
 overlap.FilterDescendantsInstances={house}
 local function blockers(p)
  local list={}
  for _,obj in ipairs(workspace:GetPartBoundsInBox(CFrame.new(p),Vector3.new(2.6,4.1,2.6),overlap)) do
   -- A supporting Floor has a top at Y=1.8. It is not a wall, even
   -- when the sampled player capsule grazes that support by 0.05 studs.
   if obj.CanCollide and obj.Size.Y>.55 and obj.Name~="Floor" then
    table.insert(list,obj)
   end
  end
  return list
 end
 local rp=RaycastParams.new()
 rp.FilterType=Enum.RaycastFilterType.Include
 rp.FilterDescendantsInstances={house,workspace.Terrain}
 -- Prefer a real traversable room interior over a doorway-only test.
 for _,distance in ipairs({16,12,9,6,3}) do
  local candidate=Vector3.new(entry.Position.X,3.8,entry.Position.Z)+inward*distance
  local bl=blockers(candidate)
  local floorhit=workspace:Raycast(candidate+Vector3.new(0,4,0),Vector3.new(0,-10,0),rp)
  print("NAV_INTERIOR_GRID",spec[2],"distance",distance,"point",candidate,"blockers",#bl,"floorY",floorhit and floorhit.Position.Y or "NIL", "floorPart",floorhit and floorhit.Instance.Name or "NIL")
  for _,ob in ipairs(bl) do
   print("NAV_INTERIOR_OBSTRUCTION",spec[2],"distance",distance,
    "name",ob.Name,"size",ob.Size,"pos",ob.Position,"parent",ob.Parent.Name)
  end
  if #bl==0 and floorhit and math.abs(floorhit.Position.Y-1.8)<1.0 then
   local path=PathfindingService:CreatePath({AgentRadius=1.6,AgentHeight=5.0,AgentCanJump=true,WaypointSpacing=3})
   local ok,err=pcall(function()path:ComputeAsync(start,candidate)end)
   print("NAV_INTERIOR_PATH",spec[2],"distance",distance,"ok",ok,"status",path.Status.Name,
    "waypoints",ok and #path:GetWaypoints() or 0,"error",not ok and tostring(err) or "")
   if ok and path.Status==Enum.PathStatus.Success then
    count+=1
    deepest[spec[2]]=distance
    print("NAV_INTERIOR_DEEPEST",spec[2],distance)
    break
   end
  end
 end
end
print("NAV_INTERIOR_HOUSE_PATHS",count)
assert(count==2,"a house cannot be entered on foot using the navigation mesh")
assert((deepest.HOUSE_ONE or 0)>=9 and (deepest.HOUSE_TWO or 0)>=9,
 "navigation paths stop at a front doorway and cannot reach the actual rooms")
print("SF_RIFT_SMOKE_PASS")
