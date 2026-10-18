local RunService=game:GetService("RunService")
RunService:Run()
task.wait(3)
local success,problem=pcall(function()
local world=workspace:WaitForChild("RiftRaidersWorld",20)
assert(world,"missing world")
local Discovery=require(game:GetService("ServerScriptService"):
 WaitForChild("SuburbanDiscovery"))
assert(#Discovery.Sites==8,"discovery trail should have eight collectible locations")
local emptyDiscovery=Discovery.Normalize(nil)
assert(Discovery.Count(emptyDiscovery)==0,"new exploration collection must be empty")
local afterReset=Discovery.Normalize({day=0,found={true,true,true}})
assert(Discovery.Count(afterReset)==0,"expired collectibles must reset daily")
local now=os.date("!*t")
local currentDay=now.year*10000+now.month*100+now.day
local partial=Discovery.Normalize({day=currentDay,found={true,true,false,true, ["HACKED"]=true}})
assert(Discovery.Count(partial)==3 and partial.found.HACKED==nil,
 "discovery progress must sanitize unknown achievements")
local discoveryFolder=world:FindFirstChild("Suburban Discovery Trail")
assert(discoveryFolder and discoveryFolder:GetAttribute("CollectibleCount")==8,
 "hidden explorer keepsakes were not placed")
assert(discoveryFolder:GetAttribute("OwnershipValidatedByServer")==true,
 "collectibles missing server validation")
for i=1,8 do
 local hidden=discoveryFolder:FindFirstChild("Hidden Keepsake "..i)
 assert(hidden and hidden:FindFirstChild("Discover Keepsake Prompt"),
  "hidden collectible not reachable "..i)
end
local Goals=require(game:GetService("ServerScriptService"):
 WaitForChild("ProgressionGoals"))
assert(#Goals.Intro==4,"new player quest sequence missing")
assert(#Goals.Daily==4,"repeatable daily goals missing")
assert(Goals.Normalize(nil).intro==0,"new player introduction must be uncompleted")
assert(Goals.Normalize({intro=900}).intro==4,"illegal intro stage not sanitized")
assert(Goals.Normalize({intro=-14}).intro==0,"negative intro stage not sanitized")
local yesterday=Goals.DayKey(os.time()-86400)
local afterDay=Goals.Normalize({day=yesterday,intro=2,counters={10,10,10,10}})
assert(afterDay.intro==2 and afterDay.completed==0 and
 afterDay.counters[1]==0,"daily goals should reset at UTC date rollover")
local sameDay=Goals.Normalize({day=Goals.DayKey(),
 intro=3,counters={1,1,1,1}})
assert(sameDay.intro==3 and sameDay.completed==4,
 "legitimate completed day should preserve four paid achievements")
local prevDay=Goals.DayKey(os.time()-86400)
local nextDay=Goals.DayKey(os.time())
assert(nextDay>=prevDay,"day keys must increase monotonically")
-- Atomic DataStore locking and migration rules, exercised against a
-- synchronous fake store. No owner account or live DataStore reads/writes.
local Persistence=require(game:GetService("ServerScriptService"):WaitForChild("DataPersistence"))
local fake={records={}}
function fake:UpdateAsync(key,fn)
 local nextValue=fn(self.records[key])
 if nextValue~=nil then self.records[key]=nextValue end
 return nextValue
end
local dataKey="Player_StudioTest"
local ok,first=Persistence.Acquire(fake,dataKey,"ServerA",10)
assert(ok and first._session.id=="ServerA","first-session lock acquisition failed")
local blocked=Persistence.Acquire(fake,dataKey,"ServerB",10)
assert(not blocked,"other server must not overwrite an active session")
local stored,versioned=Persistence.Save(fake,dataKey,"ServerA",
 {version=10,coins=123,life={career="GARDENER"}},false,10)
assert(stored and versioned.coins==123 and versioned._session.id=="ServerA",
 "in-session save did not preserve ownership")
local hijack=Persistence.Save(fake,dataKey,"ServerB",
 {version=10,coins=90000},false,10)
assert(not hijack and fake.records[dataKey].coins==123,
 "rejected server overwrote another player's coins")
local released,final=Persistence.Save(fake,dataKey,"ServerA",
 {version=10,coins=190},true,10)
assert(released and final._session==nil and final.coins==190,
 "final save did not release session safely")
local acquiredSecond,second=Persistence.Acquire(fake,dataKey,"ServerB",10)
assert(acquiredSecond and second.coins==190,
 "new server must reload latest saved coins after a clean leave")
fake.records[dataKey]._session.expiresAt=os.time()-2
local recovered,third=Persistence.Acquire(fake,dataKey,"ServerC",10)
assert(recovered and third.coins==190,
 "expired abandoned sessions must be recoverable without losing progress")
local corruptSave=Persistence.Save(fake,dataKey,"ServerB",
 {version=10,coins=666},false,10)
assert(not corruptSave and fake.records[dataKey].coins==190,
 "stale server should not overwrite re-acquired profile")
fake.records[dataKey].version=999
local futureBlocked=Persistence.Acquire(fake,dataKey,"ServerC",10)
assert(not futureBlocked,"newer profile versions must not be downgraded")
local orphanStore={records={}}
function orphanStore:UpdateAsync(key,callback)
 local result=callback(self.records[key])
 if result~=nil then self.records[key]=result end
 return result
end
assert(Persistence.Acquire(orphanStore,"Orphan","DisconnectedPlayer",10))
assert(Persistence.Release(orphanStore,"Orphan","DisconnectedPlayer"),
 "players leaving during profile initialization must release the lock")
local reacquired,orphan=Persistence.Acquire(orphanStore,"Orphan","NewServer",10)
assert(reacquired and orphan._session.id=="NewServer",
 "released orphan profile must accept new server immediately")
print("SF_RIFT_CHECK persistence_session_isolation PASS")
local imported=workspace:FindFirstChild("OfficialModernCityDistrict")
assert(imported and imported:IsA("Model"),"official modern city missing")
assert(imported:GetAttribute("ImportedScriptsRemoved")==true,"imported script safety missing")
assert(imported:GetAttribute("LifeSimulationIntegrated")==true,"downtown life integration missing")
assert(imported:GetAttribute("DowntownCareerCount")==60,"downtown career count mismatch")
assert(imported:GetAttribute("LivingDowntownIntegrated")==true,"living downtown integration missing")
local living=world:WaitForChild("Living Modern Downtown",20)
assert(living:WaitForChild("Downtown Citizen 8",20),"R15 downtown citizens missing")
assert(living:WaitForChild("Downtown Traffic Sedan 4",20),"detailed downtown traffic missing")
local vehicleTraffic=living:FindFirstChild("Downtown Traffic Sedan 1")
local bumper=vehicleTraffic:FindFirstChild("bumper_front",true)
local rear=vehicleTraffic:FindFirstChild("bumper_back",true)
assert(bumper and rear,"official traffic front/rear markers missing")
assert((bumper.Position-rear.Position):Dot(vehicleTraffic:GetPivot().LookVector)>5,
 "traffic is moving visually BACKWARDS rather than towards its headlights")
local trafficBox,trafficSize=vehicleTraffic:GetBoundingBox()
local trafficBottom=trafficBox.Position.Y-trafficSize.Y/2
assert(math.abs(trafficBottom-1.1)<.2,
 "road traffic wheels float above asphalt or sink beneath it")
assert(vehicleTraffic:GetAttribute("ForwardFacingTraffic")==true,
 "traffic heading contract missing")
print("SF_RIFT_CHECK traffic_headlights_forward_and_wheels_grounded PASS")
local walkin=world:WaitForChild("Real Walk-In Downtown Shops",20)
assert(walkin:GetAttribute("WalkInShopCount")==2 and
 walkin:GetAttribute("TeleportEntranceCount")==0,
 "two genuinely traversable street-facing shops missing")
for _,storeName in ipairs({"Accessible Corner Market","Accessible Bean and Brew"}) do
 local store=walkin:FindFirstChild(storeName)
 local door=store and store:GetAttribute("DoorCenter")
 assert(door and store:GetAttribute("DoorClearWidth")>=10,
  "missing physically open shop door: "..storeName)
 assert(door.Z>store:GetAttribute("InsideCenter").Z, "shop door faces AWAY from downtown approach")
 local ramp=store:FindFirstChild("Continuous Public Entrance Ramp")
 assert(ramp and ramp.Position.Z>door.Z, "ramp must extend toward city-facing entrance")
 assert(ramp and ramp.CanCollide and ramp:GetAttribute("AccessibilityRamp"),
  "missing traversable ground-to-door access: "..storeName)
 local params=OverlapParams.new()
 params.MaxParts=75
 local intrusions={}
 for _,node in ipairs(workspace:GetPartBoundsInBox(CFrame.new(door),
  Vector3.new(7,5,2.1),params)) do
  if node.CanCollide and not node:IsDescendantOf(store) then
   table.insert(intrusions,node:GetFullName())
  end
 end
 assert(#intrusions==0,"imported collision blocks "..storeName.." doorway: "..table.concat(intrusions," | "))
 print("SF_RIFT_WALKIN_DOOR_CLEAR "..storeName.." outside_blockers="..
  #intrusions.." "..table.concat(intrusions," | "):sub(1,420))
end
local outsideCounts={}
for _,z in ipairs({2170,2190,2210}) do
 local blockers={}
 for _,node in ipairs(workspace:GetPartBoundsInBox(CFrame.new(-15,6,z),
  Vector3.new(7,7,6))) do
  if node.CanCollide and not node:IsDescendantOf(walkin) then
   table.insert(blockers,node.Name)
  end
 end
 outsideCounts[#outsideCounts+1]=#blockers
 print("SF_RIFT_ARCADE_ACCESS_AUDIT z="..z.." blockers="..#blockers..
  " "..table.concat(blockers,","):sub(1,290))
end
local arch=world:WaitForChild("Official Detailed Suburban Town",20)
for _,name in ipairs({
 "Suburban Single Story House","Suburban Two Story House",
 "Suburban Convenience Market","Suburban Gas Station",
 "Suburban Detailed Garage",
}) do
 local prefab=arch:FindFirstChild(name)
 assert(prefab and prefab:GetAttribute("GroundLevelBottom")==.60,
  "suburban prefab was not lowered onto real ground: "..name)
 local cf,extents=prefab:GetBoundingBox()
 assert(math.abs((cf.Position.Y-extents.Y/2)-.60)<.15,
  "floating house/shop prefab at "..name)
end
print("SF_RIFT_CHECK suburban_buildings_grounded PASS")
local Access=require(game:GetService("ServerScriptService"):WaitForChild("SuburbanAccess"))
assert(arch:GetAttribute("RestoredSuburbanEntrances")==6,
 "original suburban doors still unlinked to server interactions")
assert(arch:GetAttribute("InertImportedClickDetectorsRemoved")>=100,
 "dead imported ClickDetector controls still present")
-- Studio RunScript can require a module in a distinct VM from game scripts.
-- Verify actual Workspace doors rather than a second VM's private module cache.
local observed={}
for _,instance in ipairs(arch:GetDescendants()) do
 if instance:IsA("BasePart") then
  local key=instance:GetAttribute("DoorAccessKey")
  if key then
   assert(not observed[key],"duplicate imported entrance for "..key)
   observed[key]=instance
  end
 end
end
local found=0
for _ in pairs(observed) do found+=1 end
assert(found==6,"expected six unique physical entries, got "..found)
for _,key in ipairs({
 "HOUSE_ONE","HOUSE_TWO","MARKET","GARAGE_PEDESTRIAN",
 "GARAGE_BAY_1","GARAGE_BAY_2",
}) do
 local marker=observed[key]
 assert(marker and marker:GetAttribute("OpeningPanelCount")>0,
  "missing playable original door "..key)
 assert(marker:FindFirstChildOfClass("ProximityPrompt"),
  "imported door lacks an accessible physical interaction "..key)
 assert(not marker.CanCollide and not marker.CanQuery,
  "invisible entry marker collides with players")
end
assert(arch:FindFirstChild("Suburban Convenience Market")
 :GetAttribute("RealInteriorCheckout")==true,
 "existing market counter isn't available for real shopping")
assert(arch:FindFirstChild("Suburban Detailed Garage")
 :GetAttribute("RealInteriorDealer")==true,
 "existing detailed garage hasn't been activated as a shop")
local originalMarket=arch:FindFirstChild("Suburban Convenience Market")
local importedCounter=originalMarket:FindFirstChild("Counter",true)
local counterPart=importedCounter and importedCounter:FindFirstChildWhichIsA("BasePart",true)
assert(counterPart and counterPart:GetAttribute("RegisteredSuburbanInteraction")=="SNACK" and
 counterPart:FindFirstChildOfClass("ProximityPrompt"),
 "original imported market register does not offer server-checked shopping")
local importedDealer=arch:FindFirstChild("Walk-In Auto Dealer Interior",true)
assert(importedDealer and importedDealer:GetAttribute("RegisteredSuburbanInteraction")=="STORE" and
 importedDealer:FindFirstChildOfClass("ProximityPrompt"),
 "imported auto garage interior has no vehicle dealer interaction")
print("SF_RIFT_CHECK restored_six_suburban_entries_and_indoor_shopping PASS")
task.wait(1)
local meshCount=0
for _,obj in ipairs(imported:GetDescendants()) do
 if obj:IsA("MeshPart") then meshCount+=1 end
 assert(not obj:IsA("LuaSourceContainer"),"unsafe imported script found")
end
assert(meshCount>=1000,"official detailed 3D meshes missing")
local downtownCF,downtownSize=imported:GetBoundingBox()
print("SF_MODERN_BOUNDS",downtownCF.Position,downtownSize)
local closeParts=0
for _,obj in ipairs(imported:GetDescendants()) do
 if obj:IsA("BasePart") and math.abs(obj.Position.X)<12 and
  math.abs(obj.Position.Z-2350)<12 and obj.Position.Y<35 then
  closeParts+=1
  if closeParts<=10 then print("SF_MODERN_SPAWN_NEAR",obj.Name,obj.Position) end
 end
end
print("SF_MODERN_SPAWN_NEAR_COUNT",closeParts)
local sedan=game:GetService("ServerStorage"):FindFirstChild("OfficialSedanVisual")
assert(sedan and sedan:IsA("Model"),"official car art missing")
local carMeshCount=0
for _,obj in ipairs(sedan:GetDescendants()) do
 if obj:IsA("MeshPart") then carMeshCount+=1 end
 assert(not obj:IsA("LuaSourceContainer"),"unsafe imported car script found")
end
assert(carMeshCount>=35,"detailed official sedan geometry missing")
local Styles=require(game:GetService("ServerScriptService"):WaitForChild("VehicleStyles"))
local vehicleShapes={"PICKUP_TRUCK","SUV","ELECTRIC_CAR",
 "SUPERCAR","HYPERCAR","CLASSIC_CAR"}
for _,id in ipairs(vehicleShapes) do
 local specimen=Styles.Build(workspace,CFrame.new(400,1100,0),id)
 assert(specimen and #specimen:GetDescendants()>=30,
  "custom 3D vehicle body incomplete: "..id)
 assert(specimen:GetAttribute("Silhouette")~="",
  "custom car silhouette not labeled: "..id)
 local tires=0
 for _,part in ipairs(specimen:GetDescendants()) do
  if part.Name=="Detailed Radial Tire" then tires+=1 end
  assert(not part:IsA("LuaSourceContainer"),
   "unsafe vehicle artwork script found: "..id)
 end
 assert(tires==4,"incorrect wheel geometry in "..id)
 specimen:Destroy()
end
local redSedan=game:GetService("ServerStorage"):FindFirstChild("OfficialRedSedanVisual")
assert(redSedan and redSedan:IsA("Model"),"official red sedan missing")
local redMeshes=0
for _,obj in ipairs(redSedan:GetDescendants()) do
 if obj:IsA("MeshPart") then redMeshes+=1 end
 assert(not obj:IsA("LuaSourceContainer"),"unsafe red car script found")
end
assert(redMeshes>=35,"detailed red sedan geometry incomplete")
local racing=game:GetService("ServerStorage"):FindFirstChild("OfficialRacingCarVisual")
assert(racing and racing:IsA("Model"),"official Racing template car art missing")
local raceMeshes=0
for _,obj in ipairs(racing:GetDescendants()) do
 if obj:IsA("MeshPart") then raceMeshes+=1 end
 assert(not obj:IsA("LuaSourceContainer"),
  "untrusted Racing template script imported")
end
assert(raceMeshes==29,"official Racing car should preserve 29 detailed MeshParts")
local pack=game:GetService("ServerStorage"):FindFirstChild("OfficialSuburbanArchitecture")
assert(pack and pack:IsA("Model"),"official Suburban environment pack missing")
assert(#pack:GetChildren()==6,"not all six official suburban architecture models imported")
for _,o in ipairs(pack:GetDescendants()) do
 assert(not o:IsA("LuaSourceContainer"),
  "unsafe official Suburban template code imported")
end
assert(world:FindFirstChild("Downtown Wayfinding"),"downtown portal missing")
local plaza=world:FindFirstChild("Downtown First Minute Plaza")
assert(plaza and plaza:GetAttribute("WelcomeVisible")==true,
 "cinematic first-minute plaza missing")
-- Public Bloxburg/Berry Avenue gameplay review: recognizable places,
-- street furniture and affordable early activities near arrival.
local streets=world:FindFirstChild("Detailed Downtown Streetscape")
assert(streets and streets:IsA("Folder"),
 "official detailed downtown street polish absent")
assert(streets:GetAttribute("OfficialDecorativeMeshModels")>=15,
 "street scene not populated with official Modern City mesh assets")
assert(streets:GetAttribute("TransitStopCount")==3 and
 streets:GetAttribute("TransitAccessible")==true,
 "bus stop not connected to three actual game destinations")
assert(streets:GetAttribute("ZeroExtraHeartbeatLoops")==true,
 "street visual polish should not add background animation loops")
for _,name in ipairs({
 "Urban Transit Curbside","Bus Stop Tinted Glass","Marked Pedestrian Crossing",
 "City Traffic Signal Pole","Recognizable Venue THE BEAN & BREW",
 "Recognizable Venue MOTOR ROW","Recognizable Venue CITY LIFE",
}) do
 if name=="Bus Stop Tinted Glass" then name="Bus Stop Tempered Glass" end
 assert(streets:FindFirstChild(name), "missing visible downtown street scene: "..name)
end
for _,name in ipairs({"CITY JOBS","GARDEN","HOMES"}) do
 local node=streets:FindFirstChild("Transit Stop "..name)
 assert(node and node:FindFirstChildOfClass("ProximityPrompt"),
 "free transit prompt missing "..name)
end
local CollectionService=game:GetService("CollectionService")
local tagged=CollectionService:GetTagged("RROptionalStreetscape")
assert(#tagged>=30,"visual detail mobile tier not marked for culling")
for _,desc in ipairs(streets:GetDescendants()) do
 assert(not desc:IsA("LuaSourceContainer"),
 "imported streetscape contains unsafe third-party scripts")
end
assert(plaza:GetAttribute("ImportedMeshTrees")>=4,
 "real imported city mesh trees not framing spawn")
assert(plaza:GetAttribute("ArrivalInteractionCount")==1,
 "welcome kiosk should guide new players into an active destination")
local tourist=plaza:FindFirstChild("First Minute Explore Kiosk")
local visitorPrompt=tourist and tourist:FindFirstChild("Arrival EXPLORE SUBURBIA")
assert(visitorPrompt and visitorPrompt:IsA("ProximityPrompt"),
 "interactive welcome visitor kiosk missing")
assert(plaza:FindFirstChild("Reflective Fountain Water") and
 plaza:FindFirstChild("City Brick Flowerbed") and
 plaza:FindFirstChild("Plaza Cedar Seat") and
 plaza:FindFirstChild("Welcome to RiftLife City"),
 "plaza needs active street furniture, plants and wayfinding")
local pavers=0
for _,piece in ipairs(plaza:GetChildren()) do
 if piece.Name=="Sandstone Plaza Paver" then pavers+=1 end
end
assert(pavers==40,"plaza must break up bare asphalt with sandstone paving")
local heading=world:FindFirstChild("RiftRaidersSpawn").CFrame.LookVector
assert(heading.X<-.5 and heading.Z>.1,
 "players must face actual city storefronts, not vacant gray street")
assert(imported:FindFirstChild("Modern City Asphalt Foundation"),"downtown ground missing")
assert(workspace.StreamingEnabled==true,"streaming must be enabled for mobile")
assert(game:GetService("MaterialService"):FindFirstChild("PaintedBrick"),
 "official modern city material variants missing")
assert((world:FindFirstChild("RiftRaidersSpawn").Position-Vector3.new(0,1.5,2215)).Magnitude<2,
 "downtown not the default spawn")
assert(world:GetAttribute("Version")=="0.26.0","version mismatch")
assert(world:GetAttribute("StudioSavesIsolated")==true,
 "Studio must never write a production profile data store")
local function count(name)
 local n=0
 for _,v in ipairs(world:GetDescendants()) do if v.Name==name then n+=1 end end
 return n
end
assert(count("Life City Simulation")==1,"life city missing")
assert(count("Residential Estates Neighborhood")==1,
 "residential neighborhood missing")
local estates=world:FindFirstChild("Residential Estates Neighborhood",true)
assert(estates:FindFirstChild("Home Plot 1") and
 estates:FindFirstChild("Home Plot 12"),
 "twelve property plots not built")
assert(count("Residential Asphalt Road")==2,"neighborhood roads missing")
local suburbs=world:FindFirstChild("Official Detailed Suburban Town")
assert(suburbs and suburbs:GetAttribute("OfficialPrefabCount")==6,
 "Suburban detailed environment not actually spawned")
assert(suburbs:GetAttribute("DetailedSourceParts")>5000,
 "Detailed suburban city parts missing")
assert(suburbs:GetAttribute("MicroDecorOptimized")>=100,
 "tiny suburban decorations should avoid expensive collisions/shadows")
assert(suburbs:GetAttribute("PreservedWalkableColliderParts")>100,
 "suburban building floors or walls lost their physical collision")
assert(suburbs:GetAttribute("StreamingAware")==true,
 "imported world must stream over long distances")
assert(suburbs:GetAttribute("EnvironmentOnly")==false,
 "Imported suburban town must contain actual playable economic services")
assert(suburbs:GetAttribute("ActiveSuburbanWorkplaces")==4,
 "Detailed suburb career shifts missing")
assert(suburbs:GetAttribute("ServerValidatedServicePoints")>=21,
 "Server-registered suburban shop and career points missing")
local realSuburbanServices=world:FindFirstChild("Working Suburban Services",true)
assert(realSuburbanServices,"Real template-based suburban services missing")
for _,name in ipairs({
 "Official Suburban Market Checkout","Official Suburban Auto Garage Checkout",
 "Official Suburban Gas Station Kiosk","Suburban Play Park Rest Station",
 "Suburban Worksite RETAIL","Suburban Work Task RETAIL 1",
 "Suburban Work Task RETAIL 2","Suburban Worksite MECHANIC",
 "Suburban Work Task MECHANIC 1","Suburban Work Task MECHANIC 2",
}) do
 local node=realSuburbanServices:FindFirstChild(name)
 assert(node and node:IsA("BasePart"),"Missing usable suburb station: "..name)
 assert(node:GetAttribute("RegisteredSuburbanInteraction")~=nil,
  "Unregistered suburb station: "..name)
end
assert(suburbs:FindFirstChild("Suburban Single Story House")
 and suburbs:FindFirstChild("Suburban Two Story House")
 and suburbs:FindFirstChild("Suburban Convenience Market")
 and suburbs:FindFirstChild("Suburban Gas Station")
 and suburbs:FindFirstChild("Suburban Playground"),
 "Missing genuine detailed suburban building prefab")
assert(estates:GetAttribute("OfficialMeshTrees")==12,
 "estate official mesh-tree landscaping not installed")
assert(count("Modern Downtown Life Services")==1,"downtown life services missing")
assert(count("Living Modern Downtown")==1,"living downtown folder missing")
assert(count("Downtown Citizen 1")==1 and count("Downtown Citizen 8")==1,
 "downtown R15 citizen count missing")
assert(count("Downtown Traffic Sedan 1")==1 and count("Downtown Traffic Sedan 4")==1,
 "downtown detailed traffic count missing")
for i=1,8 do
 local citizen=world:FindFirstChild("Downtown Citizen "..i,true)
 local hum=citizen and citizen:FindFirstChildOfClass("Humanoid")
 assert(hum and hum.RigType==Enum.HumanoidRigType.R15,"downtown citizen is not R15")
 local accessory=citizen and citizen:FindFirstChildOfClass("Accessory")
 assert(accessory,"downtown citizen hair/accessory missing")
 local talk=citizen and citizen:FindFirstChild("Talk to Citizen",true)
 assert(talk and talk:IsA("ProximityPrompt"),"downtown citizen talk prompt missing")
 assert(type(citizen:GetAttribute("CitizenName"))=="string","citizen name missing")
end
assert(world:GetAttribute("DowntownConversations")==0,"conversation counter initialization missing")
assert((world:GetAttribute("DowntownTrafficDistance") or 0)>0,
 "downtown traffic did not move")
assert((world:FindFirstChild("Downtown Traffic Sedan 1",true):GetAttribute("DistanceTravelled") or 0)>0,
 "detailed traffic distance attribute missing")
assert(count("Downtown Employment Center")==1,"downtown employment office missing")
assert(count("Downtown Store GARDEN")==1,"downtown nursery store missing")
assert(count("Downtown Worksite GARDENER")==1,"new gardener worksite missing")
local cafe=world:FindFirstChild("Downtown Interactive Coffee Bar")
assert(cafe and cafe:GetAttribute("InteractiveOrders")==true,
 "new barista cafe must contain real physical customer-order gameplay")
for _,coffee in ipairs({"ESPRESSO","LATTE","MOCHA"}) do
 local node=cafe:FindFirstChild("Coffee Brew "..coffee)
 assert(node and node:FindFirstChildOfClass("ProximityPrompt"),
  "interactive coffee recipe missing: "..coffee)
end
assert(cafe:FindFirstChild("Cafe Customer Service Register") and
 cafe:FindFirstChild("Solid Oak Service Counter"),
 "coffee service window and detail missing")
-- Second tactile workplace: official racing MeshParts are a visible
-- demo car while the service loop itself is independently server checked.
local mechanicBay=world:FindFirstChild("Pit Stop Detailed Mechanic Bay")
assert(mechanicBay and mechanicBay:GetAttribute("MechanicFaultTypes")==3,
 "three-fault interactive auto repair garage missing")
assert(mechanicBay:GetAttribute("RequiresRealInspection")==true and
 mechanicBay:GetAttribute("NoBackgroundLoops")==true,
 "service flow should be physical and efficient")
local importedDemo=mechanicBay:FindFirstChild("Official Racing Service Demo Car")
assert(importedDemo and importedDemo:IsA("Model"),
 "actual official detailed racing car absent from repair bay")
local repairMeshes=0
for _,piece in ipairs(importedDemo:GetDescendants()) do
 if piece:IsA("MeshPart") then repairMeshes+=1 end
 assert(not piece:IsA("LuaSourceContainer"),"untrusted demo car code inserted")
end
assert(repairMeshes==29,"demo car should retain 29 official racing meshes")
local mechanic=require(game:GetService("ServerScriptService"):WaitForChild("MechanicService"))
for _,fault in ipairs({"BRAKES","BATTERY","TIRES"}) do
 local workbench=mechanicBay:FindFirstChild("Repair Station "..fault)
 assert(workbench and workbench:FindFirstChildOfClass("ProximityPrompt"),
  "actual repair workbench missing "..fault)
end
assert(mechanicBay:FindFirstChild("Fault Diagnostic Tablet"):FindFirstChildOfClass("ProximityPrompt"),
 "working repair fault scanner not accessible")
local mechanicShift={id="MECHANIC",started=os.clock()-5,progress=0,taskAt=0}
local fault=mechanic.Assign(mechanicShift)
assert(table.find(mechanic.Faults,fault) and not mechanicShift.mechanicScanned,
 "randomized mechanical fault assignment missing")
local market=world:FindFirstChild("Downtown Hands-On Corner Market")
assert(market and market:GetAttribute("RetailSkuCount")==3 and
 market:GetAttribute("ServerValidatedOrder")==true and
 market:GetAttribute("NoBackgroundLoops")==true,
 "physical retail checkout and restock loop missing")
local retail=require(game:GetService("ServerScriptService"):WaitForChild("RetailService"))
for _,sku in ipairs(retail.Products) do
 local scan=market:FindFirstChild("Retail Checkout "..sku)
 local restock=market:FindFirstChild("Retail Restock "..sku)
 assert(scan and scan:FindFirstChildOfClass("ProximityPrompt"),
  "retail checkout must have actual prompt: "..sku)
 assert(restock and restock:FindFirstChildOfClass("ProximityPrompt"),
  "retail shelf must have actual prompt: "..sku)
end
local sampleRetail={id="RETAIL",started=os.clock()-5,progress=0,taskAt=0}
local item,stock=retail.Assign(sampleRetail)
assert(table.find(retail.Products,item) and table.find(retail.Products,stock)
 and not sampleRetail.retailScanned,
 "server-selected retail order or restock SKU missing")
local courierDepot=world:FindFirstChild("Downtown Hands-On Delivery Depot")
assert(courierDepot and courierDepot:GetAttribute("CourierParcelTypes")==3 and
 courierDepot:GetAttribute("CourierDestinationTypes")==3 and
 courierDepot:GetAttribute("ServerValidatedDelivery")==true and
 courierDepot:GetAttribute("NoBackgroundLoops")==true,
 "physical courier route and dispatch/depot missing")
local courier=require(game:GetService("ServerScriptService"):WaitForChild("CourierService"))
for _,parcel in ipairs(courier.Parcels) do
 local bin=courierDepot:FindFirstChild("Courier Pickup "..parcel)
 assert(bin and bin:FindFirstChildOfClass("ProximityPrompt"),
  "pickup bin missing "..parcel)
end
for _,destination in ipairs(courier.Destinations) do
 local stop=courierDepot:FindFirstChild("Courier Dropoff "..destination)
 assert(stop and stop:FindFirstChildOfClass("ProximityPrompt"),
  "delivery door missing "..destination)
end
assert(courierDepot:GetAttribute("CourierNPCCount")==4,
 "courier receivers and depot dispatcher missing")
local cashier=market:FindFirstChild("Corner Market Cashier A")
local shoe=cashier and cashier:FindFirstChild("Left Shoe",true)
assert(shoe and math.abs(shoe.Position.Y-shoe.Size.Y/2-2.775)<.17,
 "retail character feet are hovering above the indoor floor")
local dispatcher=courierDepot:FindFirstChild("Rift Express Dispatcher")
local dispatchShoe=dispatcher and dispatcher:FindFirstChild("Left Shoe",true)
assert(dispatchShoe and math.abs(dispatchShoe.Position.Y-
 dispatchShoe.Size.Y/2-2.75)<.17,
 "courier dispatcher feet hover above depot floor")
print("SF_RIFT_CHECK venue_characters_foot_contact PASS")
assert(market:GetAttribute("RetailNPCCount")==2,
 "retail cashier and customer helper missing")
for _,folder in ipairs({market,courierDepot}) do
 local count=0
 for _,npc in ipairs(folder:GetChildren()) do
  if npc:IsA("Model") and npc:GetAttribute("NPCType")=="StaticWorkplaceGuide" then
   count+=1
   assert(npc.PrimaryPart and npc.PrimaryPart:FindFirstChildOfClass("ProximityPrompt"),
    "customer directions cannot be requested")
   for _,node in ipairs(npc:GetDescendants()) do
    assert(not node:IsA("LuaSourceContainer"),"untrusted marketplace NPC code")
   end
  end
 end
 assert(count==folder:GetAttribute(folder==market and "RetailNPCCount" or
  "CourierNPCCount"),"NPC count mismatch")
end
local sampleCourier={id="COURIER",started=os.clock()-5,progress=0,taskAt=0}
local parcel,address=courier.Assign(sampleCourier)
assert(table.find(courier.Parcels,parcel) and
 table.find(courier.Destinations,address) and
 not sampleCourier.courierPickedUp,"courier assignment invalid")
local CafeService=require(game:GetService("ServerScriptService"):WaitForChild("CafeService"))
local coffeeShift={id="BARISTA",started=os.clock()-5,progress=0,taskAt=0}
local selectedOrder=CafeService.Assign(coffeeShift)
assert(table.find(CafeService.Recipes,selectedOrder) and
 coffeeShift.cafeOrder==selectedOrder and not coffeeShift.cafeBrewed,
 "server-assigned randomly selected barista drink missing")
assert(count("Downtown Job Task BOAT_CAPTAIN 2")==1,
 "boat captain interactive work task missing")
assert(count("Downtown Community Garden")==1,"community garden missing")
assert(count("Raised Garden Bed 1")==1 and count("Raised Garden Bed 16")==1,
 "interactive garden plots missing")
assert(count("Downtown Farm Produce Market")==1,"garden market missing")
assert(count("Navigable Ocean Marina")==1,"drivable ocean marina missing")
assert(count("Public Marina Boat Launch")==1,"boat launch dock missing")
local Boats=require(game:GetService("ServerScriptService"):WaitForChild("BoatService"))
assert(Boats.Vessels.SPEEDBOAT.speed>Boats.Vessels.FISHING_BOAT.speed,
 "speedboat speed model invalid")
assert(Boats.Vessels.LUXURY_YACHT.length>Boats.Vessels.SPEEDBOAT.length,
 "yacht model dimensions invalid")
local Garden=require(game:GetService("ServerScriptService"):WaitForChild("UrbanGardening"))
assert(#Garden.Order==14,"crop varieties missing")
assert(Garden.Normalize(nil).crop=="","new garden should be empty")
local savedGarden=Garden.Normalize({crop="TOMATO_SEEDS",plantedAt=os.time()-75,
 watered=true,produce={TOMATO_SEEDS=3,BAD_ITEM=900}})
assert(Garden.Status(savedGarden)=="READY","offline mature crop growth failed")
assert(savedGarden.produce.BAD_ITEM==nil and savedGarden.produce.TOMATO_SEEDS==3,
 "garden crop inventory allowlist failed")
local savedSeeds=Garden.Normalize({seeds={TOMATO_SEEDS=4,HACKED_SEEDS=99}})
assert(savedSeeds.seeds.TOMATO_SEEDS==4 and savedSeeds.seeds.HACKED_SEEDS==nil,
 "purchasable seed stock data not sanitized")
assert(count("Downtown Store TECH")==1,"downtown technology storefront missing")
assert(count("Downtown Store BUSINESS")==1,"downtown commerce storefront missing")
assert(count("Downtown Worksite RETAIL")==1,"downtown retail worksite missing")
assert(count("Downtown Worksite POLICE")==1,"downtown police worksite missing")
assert(count("Downtown Worksite PILOT")==1,"downtown pilot worksite missing")
assert(count("Downtown Job Task BARISTA 1")==1,"downtown job tasks missing")
assert(count("Career and Employment Center")==1,"career center missing")
assert(count("Creator Technology Store")==1,"technology store missing")
assert(count("Clothing Boutique")==1,"apparel store missing")
assert(count("Real Estate Agency")==1,"real estate office missing")
assert(count("Vehicle and Marine Dealer")==1,"vehicle dealer missing")
assert(count("Business Licensing Office")==1,"business office missing")
assert(count("Life City Jail")==1,"jail missing")
assert(count("Community Meal Station")==1,"free meals missing")
assert(count("Public Rest Bench")==1,"park rest missing")
assert(count("Life City Architectural Details")==1,"city details missing")
assert(count("City Streetlamp")>=4,"street lights missing")
assert(count("Street Tree 1")>=1,"street trees missing")
assert(count("Job Task PARAMEDIC 1")==1,"paramedic task missing")
assert(count("Job Task FIREFIGHTER 2")==1,"fire rescue task missing")
assert(count("Job Task PILOT 1")==1,"pilot task missing")
assert(count("Career Board VETERINARIAN")==1,"veterinary career missing")
assert(count("Fine Payment Counter")==1,"court fines missing")
assert(count("AI Police Officer 1")==1,"police AI missing")
assert(count("Media Recording Studio")==1,"creator studio missing")
local life=require(game:GetService("ReplicatedStorage"):WaitForChild("LifeCatalog"))
assert(#life.Careers==60,"careers missing")
assert(#life.Items==174,"expanded real-world catalog count changed")
assert(life.CareerById.GARDENER and life.CareerById.BOAT_CAPTAIN and
 life.CareerById.SOFTWARE_ENGINEER,"new real-life careers missing")
assert(life.ById.TOMATO_SEEDS and life.ById.GARDEN_TROWEL and
 life.ById.WATERING_CAN and life.ById.SPEEDBOAT and
 life.ById.HYPERCAR,"garden and premium vehicles missing")
assert(#life.DrivableCars==10,"ten selectable car choices missing")
assert(life.CarChoices.RACE_CAR and life.ById.RACE_CAR,
 "official Racing car shop option missing")
assert(life.CarChoices.PICKUP_TRUCK and life.CarChoices.SUV,
 "separate pickup and SUV purchases missing")
assert(life.CarChoices.HYPERCAR.speed>life.CarChoices.SEDAN.speed,
 "purchased car speed tiers invalid")
assert(life.BusinessPayouts.MARINA_BUSINESS==590,
 "new owned business revenue missing")
assert(life.ById.TABLET and life.ById.COUCH and life.ById.CONDO,
 "expanded everyday shopping catalog missing")
assert(life.BusinessPayouts.RESTAURANT_BUSINESS==230,
 "expanded business income missing")
assert(life.ById.YACHT.price==35000,"yacht pricing missing")
assert(life.ById.MANSION.level==30,"mansion level gate missing")
assert(life.SanitizeOwned({PHONE=true,HACKED=true}).HACKED==nil,
 "life catalog ownership allowlist failed")
local lifeApi=require(game:GetService("ServerScriptService"):WaitForChild("LifeSimulation"))
local fresh=lifeApi.Normalize(nil)
assert(fresh.needs.hunger==100 and fresh.needs.energy==100 and
 fresh.needs.hygiene==100,"fresh needs incorrect")
local cleaned=lifeApi.Normalize({career="HACKER",needs={hunger=-30,energy=200,hygiene=17}})
assert(cleaned.career=="UNEMPLOYED" and cleaned.needs.hunger==0 and
 cleaned.needs.energy==100 and cleaned.needs.hygiene==17,
 "life needs migration sanitization failed")
assert(lifeApi.Serialize(cleaned).needs.hygiene==17,"needs save data missing")
assert(lifeApi.Serialize(cleaned).garden.harvests==0,
 "new garden schema serialization missing")
assert(cleaned.needs.fun==100 and cleaned.homeLocked,
 "new life needs and default home security missing")
local restored=lifeApi.Normalize({owned={SEDAN=true},
 selectedCar="SEDAN",homeLocked=false,needs={fun=26}})
assert(restored.selectedCar=="SEDAN" and restored.homeLocked==false and
 restored.needs.fun==26,"legacy profile selected car/home security migration failed")
assert(lifeApi.Normalize({selectedCar="HACKED_CAR"}).selectedCar=="",
 "malicious selected vehicle failed validation")
local Architecture=require(game:GetService("ServerScriptService"):WaitForChild("HomeArchitecture"))
local livingHomes=require(game:GetService("ServerScriptService"):WaitForChild("HomeLiving"))
local sample=Instance.new("Model")
sample.Name="Studio Furniture Test House";sample.Parent=workspace
local dummy={UserId=55155}
local state={life={homeLocked=true,needs={fun=35,hunger=30,energy=60,hygiene=50}}}
Architecture.Build(sample,Vector3.new(0,500,0),29,2,"FARMHOUSE",dummy,{
 SOLAR_PANEL=true,
},{
 getProfile=function() return state end,
 tell=function() end,sync=function() end,
})
livingHomes.Furnish(sample,Vector3.new(0,500,0),29,2,dummy,{
 SMART_TV=true,GAME_CONSOLE=true,FRIDGE=true,DINING_TABLE=true,
 WASHER_DRYER=true,KING_BED=true,BABY_CRIB=true,BOOKSHELF=true,
 PET_BED=true,WORKSTATION=true,COUCH=true,
},{
 getProfile=function() return state end,
 tell=function() end,sync=function() end,
})
assert(sample:FindFirstChild("Walkable Stair Tread 3 1") and
 sample:FindFirstChild("Walkable Upper Level Floor 2") and
 sample:FindFirstChild("Upper Bedroom Mattress") and
 sample:FindFirstChild("Ground Floor Lift") and
 sample:GetAttribute("ReachableUpperFloors")==1,
 "home upper floors are not navigable or furnished")
assert(sample:FindFirstChild("Security Entrance Door")
 and sample:FindFirstChild("Wall Mounted Smart TV")
 and sample:FindFirstChild("Home Refrigerator")
 and sample:FindFirstChild("Purchased King Mattress")
 and sample:FindFirstChild("Nursery Crib Base")
 and sample:FindFirstChild("Home Washing Machine")
 and sample:FindFirstChild("Creator Work Desk"),
 "purchased home furnishing models missing")
local locked=sample:FindFirstChild("Door Smart Lock")
assert(locked and locked:GetAttribute("Locked")==true,
 "owned-home door lock validation missing")
sample:Destroy()
assert(count("Central Hub")==1,"hub missing")
assert(count("Living World Atmosphere")==1,"world polish missing")
assert(count("Ambient Pedestrian 1")==1,"pedestrian simulation missing")
assert(count("Ambient City Traffic 1")==1,"traffic missing")
assert(count("Life City Traffic 1")==1,"life city traffic missing")
assert(count("Ambient Pedestrian 18")==1,"life city citizens missing")
assert(count("Workplace Props FIREFIGHTER 2")==1,"fire training props missing")
assert(count("Workplace Props CHEF 1")==1,"chef props missing")
assert(count("City Ring Road")==4,"city road loop missing")
assert(world:GetAttribute("Weather")=="CLEAR","weather initialization missing")
assert(game:GetService("Lighting"):FindFirstChild("RiftNaturalColorGrade"),
 "natural color grading missing")
assert(workspace.Terrain:FindFirstChildOfClass("Clouds"),"dynamic clouds missing")
local catalog=require(game:GetService("ReplicatedStorage"):WaitForChild("PrestigeCatalog"))
assert(#catalog.Items>=8,"earned prestige catalog missing")
assert(catalog.ById.HOME_GARAGE.coins==6000,"garage pricing mismatch")
assert(catalog.ById.FLIGHT_LICENSE.level==12,"flight license missing")
assert(catalog.ValidateOwned({CITY_WRAP=true,HACKED=true}).HACKED==nil,
 "catalog allowed unknown item")

assert(count("Safe Skybridge")==4,"four bridges required")
assert(count("Rift Shard")==36,"36 shards required")
assert(count("Rift Drone")==12,"12 drones required")
assert(count("Rift Core CYBER")==1,"cyber beacon missing")
assert(count("Rift Core CRYSTAL")==1,"crystal beacon missing")
assert(count("Rift Core VOLCANO")==1,"volcano beacon missing")
assert(count("Rift Core SKY")==1,"sky beacon missing")
assert(count("Cloud Summit")==1,"summit missing")
assert(count("ReusableWorldKit")==1,"reusable scenery missing")
assert(count("Tree_pine")>=9,"trees missing")
assert(count("Grass Patch")>=70,"grass missing")
assert(count("Parked Future Car")==3,"parked cars missing")
assert(count("Road Segment")>=1,"roads missing")
assert(count("Chaos Titan")==1,"boss missing")
assert(count("Seven New Worlds")==1,"new regions missing")
assert(count("Courier Dispatch Terminal")==1,"courier dispatch missing")
assert(count("Interworld Delivery Point")==7,"courier dropoffs missing")
assert(count("Walkable Arrival Plaza")==7,"seven world plazas missing")
assert(count("Portal to Central Hub")==7,"return portals missing")
assert(count("Royal Stone Castle")==1,"castle missing")
assert(count("Working Farm Barn")==1,"farm missing")
assert(count("Harvest Carrot")==6,"carrot crops missing")
assert(count("Japanese Torii Gate")==1,"japan missing")
assert(count("Five-Level Pagoda")==1,"pagoda missing")
assert(count("Snowmobile Display")==4,"snowmobiles missing")
assert(count("Jetpack Station")==1,"jetpack missing")
assert(count("Marina Dock")==1,"marina missing")
assert(count("City Bank")==1,"bank missing")
assert(count("Passenger Jet Display")==1,"airport jet missing")
assert(count("Animal Body")>=6,"animals missing")
assert(count("Sports and Life Activities")==1,"activity world missing")
assert(count("Sports Plaza")==1,"sports district missing")
assert(count("Player Housing Neighborhood")==1,"housing district missing")
assert(count("Home Floor")==0,"unowned houses should not spawn in smoke")
assert(count("Housing Construction Office")==1,"housing office missing")
assert(count("Soccer Pitch")==1,"soccer pitch missing")
assert(count("Football Field")==1,"football field missing")
assert(count("Baseball Diamond")==1,"baseball diamond missing")
assert(count("Stadium Floodlight")==4,"sports floodlights missing")
for _,id in ipairs({
 "football","baseball","soccer","fishing","hunting",
 "gather_wood","gather_wood_2","gather_wood_3","gather_wood_4","gather_wood_5",
 "gather_metal","gather_metal_alt","gather_metal_alt2","gather_metal_alt3","gather_metal_alt4","craft_toolkit","sell_fish",
 "bank_heist","steal_car","chop_shop","build_house"
}) do
 local found=false
 for _,node in ipairs(world:GetDescendants()) do
  if node:GetAttribute("ActivityId")==id then found=true; break end
 end
 assert(found,"activity missing: "..id)
end
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftActivitiesSignal"),
 "activity challenge signal missing")
local terrainMaterials,terrainOccupancy=workspace.Terrain:ReadVoxels(
 Region3.new(Vector3.new(520,-8,-8),Vector3.new(528,0,0)):ExpandToGrid(4),4)
assert(terrainOccupancy[1][1][1]>.1,"castle terrain not filled")
assert(terrainMaterials[1][1][1]==Enum.Material.Grass,"castle terrain material wrong")
assert(game:GetService("ServerScriptService"):FindFirstChild("VehicleService"),"vehicle service missing")
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftRaidersAction"),"action missing")
assert(game:GetService("ReplicatedStorage"):FindFirstChild("RiftRaidersEvent"),"event missing")
end)
if success then print("SF_RIFT_SMOKE_PASS") else warn("SF_RIFT_SMOKE_FAIL "..tostring(problem)) end
RunService:Stop()
