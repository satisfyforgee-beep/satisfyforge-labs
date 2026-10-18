-- v0.6 LIFE CITY: in-game-only jobs, shops, creator career and law enforcement.
-- Server validates career, level, currency, ownership, cooldowns and proximity.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Terrain=workspace.Terrain
local Catalog=require(game:GetService("ReplicatedStorage"):WaitForChild("LifeCatalog"))
local Garden=require(script.Parent:WaitForChild("UrbanGardening"))
local Cafe=require(script.Parent:WaitForChild("CafeService"))
local Mechanic=require(script.Parent:WaitForChild("MechanicService"))
local Retail=require(script.Parent:WaitForChild("RetailService"))
local Home=require(script.Parent:WaitForChild("HomeLiving"))
local Architecture=require(script.Parent:WaitForChild("HomeArchitecture"))
local Life={}
local context,world,folder
local stores={}
local workSites={}
local careerSites={}
local taskSites={}
-- v0.9: alternate interaction anchors embedded around the imported detailed
-- Modern Downtown. The original Life City remains fully functional.
local downtownStores={}
local downtownWorkSites={}
local downtownCareerSites={}
local downtownTaskSites={}
local downtownFineCounter=nil
local downtownFoodCounter=nil
local downtownRestCounter=nil
-- Extra validated locations supplied by imported, script-free environment art.
-- This means assets can be reused without trusting any scripts from templates.
local externalStores={}
local externalCareerSites={}
local externalWorkSites={}
local externalTaskSites={}
local externalRestSites={}
local externalSnackSites={}
local policeUnits={}
local lastAction={}
local fineCounter=nil
local foodCounter=nil
local restCounter=nil
local publicMealCooldown={}
local propertySlots={}
local playerSlots={}
local playerProperties={}
local propertyBases={}
for row=0,1 do
 for col=0,5 do
  table.insert(propertyBases,Vector3.new(-155+col*62,0,2750+row*70))
 end
end
local jailCenter=Vector3.new(126,7,1655)
local townCenter=Vector3.new(0,0,1600)
local function part(parent,name,size,pos,color,material,collide)
 local p=Instance.new("Part"); p.Name=name; p.Size=size; p.Position=pos
 p.Anchored=true; p.CanCollide=collide==true; p.CanTouch=false
 p.Material=material or Enum.Material.SmoothPlastic
 p.Color=color; p.Parent=parent
 return p
end
local function textSign(parent,name,position,color)
 local anchor=part(parent,"Store Sign Anchor",Vector3.one,position,color,nil,false)
 anchor.Transparency=1
 local gui=Instance.new("BillboardGui"); gui.Size=UDim2.fromOffset(260,55)
 gui.MaxDistance=160; gui.AlwaysOnTop=true; gui.Parent=anchor
 local t=Instance.new("TextLabel"); t.Size=UDim2.fromScale(1,1)
 t.BackgroundTransparency=1; t.Text=name; t.TextScaled=true
 t.TextColor3=color; t.TextStrokeTransparency=.2
 t.Font=Enum.Font.GothamBlack; t.Parent=gui
end
local function prompt(node,actionText,objectText,callback)
 local p=Instance.new("ProximityPrompt")
 p.ActionText=actionText; p.ObjectText=objectText
 p.MaxActivationDistance=13; p.HoldDuration=.5
 p.RequiresLineOfSight=false; p.Parent=node
 p.Triggered:Connect(callback)
end
local function root(player)
 return player.Character and player.Character:FindFirstChild("HumanoidRootPart")
end
local function nearby(player,anchor,distance)
 local r=root(player)
 return r and anchor and (r.Position-anchor.Position).Magnitude<=(distance or 20)
end
local function nearbyEither(player,a,b,distance)
 return nearby(player,a,distance) or nearby(player,b,distance)
end
local function registeredNearby(player,map,id,distance)
 local options=map[id]
 if not options then return false end
 for _,point in ipairs(options) do
  if point.Parent and nearby(player,point,distance) then return true end
 end
 return false
end
function Life.RegisterSuburbanPoint(usage,id,node,step)
 if not node or not node:IsA("BasePart") then return false end
 if usage=="STORE" and Catalog.ShopLocations[id] then
  externalStores[id]=externalStores[id] or {}
  table.insert(externalStores[id],node)
 elseif usage=="CAREER" and Catalog.CareerById[id] then
  externalCareerSites[id]=externalCareerSites[id] or {}
  table.insert(externalCareerSites[id],node)
 elseif usage=="WORK" and Catalog.CareerById[id] then
  externalWorkSites[id]=externalWorkSites[id] or {}
  table.insert(externalWorkSites[id],node)
 elseif usage=="TASK" and Catalog.CareerById[id] and
  (step==1 or step==2) then
  externalTaskSites[id]=externalTaskSites[id] or {}
  externalTaskSites[id][step]=externalTaskSites[id][step] or {}
  table.insert(externalTaskSites[id][step],node)
 elseif usage=="REST" and id=="PUBLIC" then
  externalRestSites.PUBLIC=externalRestSites.PUBLIC or {}
  table.insert(externalRestSites.PUBLIC,node)
 elseif usage=="SNACK" and id=="MARKET" then
  externalSnackSites.MARKET=externalSnackSites.MARKET or {}
  table.insert(externalSnackSites.MARKET,node)
 else return false end
 node:SetAttribute("RegisteredSuburbanInteraction",usage)
 return true
end
local function nearStore(player,category,distance)
 return nearbyEither(player,stores[category],downtownStores[category],distance)
  or registeredNearby(player,externalStores,category,distance)
end
local function nearCareer(player,id,distance)
 return nearbyEither(player,careerSites[id],downtownCareerSites[id],distance)
  or registeredNearby(player,externalCareerSites,id,distance)
end
local function nearWork(player,id,distance)
 return nearbyEither(player,workSites[id],downtownWorkSites[id],distance)
  or registeredNearby(player,externalWorkSites,id,distance)
end
local function nearTask(player,id,step,distance)
 return nearbyEither(player,taskSites[id] and taskSites[id][step],
  downtownTaskSites[id] and downtownTaskSites[id][step],distance)
  or (externalTaskSites[id] and
   registeredNearby(player,externalTaskSites[id],step,distance))
end
local function profile(player)
 return context and context.getProfile(player)
end
local function tell(player,msg) context.tell(player,msg) end
function Life.Normalize(value)
 value=type(value)=="table" and value or {}
 return {
  career=Catalog.SanitizeCareer(value.career),
  owned=Catalog.SanitizeOwned(value.owned),
  garden=Garden.Normalize(value.garden),
  homeLocked=value.homeLocked~=false,
  selectedCar=type(value.selectedCar)=="string" and
   Catalog.CarChoices[value.selectedCar] and
   type(value.owned)=="table" and value.owned[value.selectedCar]==true and
   value.selectedCar or "",
  followers=math.clamp(math.floor(tonumber(value.followers) or 0),0,10000000),
  uploads=math.clamp(math.floor(tonumber(value.uploads) or 0),0,1000000),
  shifts=math.clamp(math.floor(tonumber(value.shifts) or 0),0,1000000),
  reputation=math.clamp(math.floor(tonumber(value.reputation) or 0),0,1000000),
  fines=math.clamp(math.floor(tonumber(value.fines) or 0),0,1000000),
  arrests=math.clamp(math.floor(tonumber(value.arrests) or 0),0,100000),
  needs={
   hunger=math.clamp(math.floor(tonumber(type(value.needs)=="table" and value.needs.hunger) or 100),0,100),
   energy=math.clamp(math.floor(tonumber(type(value.needs)=="table" and value.needs.energy) or 100),0,100),
   hygiene=math.clamp(math.floor(tonumber(type(value.needs)=="table" and value.needs.hygiene) or 100),0,100),
   fun=math.clamp(math.floor(tonumber(type(value.needs)=="table" and value.needs.fun) or 100),0,100),
  },
  lastWork=0,lastPost=0,lastBusiness=0,lastHome=-100,
  jailUntil=0,activeShift=nil,
 }
end
function Life.Serialize(value)
 local s=Life.Normalize(value)
 return {career=s.career,owned=s.owned,followers=s.followers,
  uploads=s.uploads,shifts=s.shifts,reputation=s.reputation,
  fines=s.fines,arrests=s.arrests,needs=s.needs,garden=s.garden,
  homeLocked=s.homeLocked,selectedCar=s.selectedCar}
end
function Life.Sync(player)
 local s=profile(player)
 if not s or not s.life then return end
 local life=s.life
 player:SetAttribute("RRLifeCareer",life.career)
 player:SetAttribute("RRLifeHomeLocked",life.homeLocked)
 player:SetAttribute("RRLifeHomePlot",
  playerProperties[player] and playerSlots[player] or 0)
 player:SetAttribute("RRLifeSelectedCar",life.selectedCar)
 player:SetAttribute("RRLifeFun",life.needs.fun)
 Garden.SyncPlayer(player,life.garden)
 player:SetAttribute("RRLifeHunger",life.needs.hunger)
 player:SetAttribute("RRLifeEnergy",life.needs.energy)
 player:SetAttribute("RRLifeHygiene",life.needs.hygiene)
 player:SetAttribute("RRLifeFollowers",life.followers)
 player:SetAttribute("RRLifeUploads",life.uploads)
 player:SetAttribute("RRLifeShifts",life.shifts)
 player:SetAttribute("RRLifeReputation",life.reputation)
 player:SetAttribute("RRLifeFines",life.fines)
 player:SetAttribute("RRLifeArrests",life.arrests)
 player:SetAttribute("RRLifeJailed",os.clock()<life.jailUntil)
 player:SetAttribute("RRLifeJailRemaining",
  math.max(0,math.ceil(life.jailUntil-os.clock())))
 for _,item in ipairs(Catalog.Items) do
  player:SetAttribute("RRLifeOwn_"..item.id,life.owned[item.id]==true)
 end
 local shift=life.activeShift
 player:SetAttribute("RRLifeShift",shift and shift.id or "")
 player:SetAttribute("RRLifeTaskStep",shift and shift.progress or 0)
 local nextTarget=shift and taskSites[shift.id] and taskSites[shift.id][shift.progress+1]
 player:SetAttribute("RRLifeCafeOrder",shift and shift.id=="BARISTA" and
  shift.cafeOrder or "")
 player:SetAttribute("RRLifeMechanicFault",shift and shift.id=="MECHANIC" and
  shift.mechanicScanned and shift.mechanicFault or "")
 player:SetAttribute("RRLifeRetailOrder",shift and shift.id=="RETAIL" and
  shift.retailScanSku or "")
 local label=shift and shift.id=="MECHANIC" and
  (shift.progress==0 and "INSPECT CAR AT PIT STOP SCANNER" or
   shift.progress==1 and "REPAIR "..(shift.mechanicFault or "CAR")..
    " AT THE MATCHING WORKBENCH" or "COLLECT YOUR MECHANIC PAYCHECK") or nil
 label=label or (shift and shift.id=="RETAIL" and shift.retailScanSku and
  (shift.progress==0 and "SCAN "..shift.retailScanSku.." AT CORNER MARKET" or
   shift.progress==1 and "RESTOCK "..shift.retailStockSku.." ON THE STORE SHELF" or
   "COLLECT YOUR RETAIL PAYCHECK") or nil)
 label=label or (shift and shift.id=="BARISTA" and
  (shift.progress==0 and "BREW "..(shift.cafeOrder or "COFFEE") or
   shift.progress==1 and "SERVE DRINK AT CUSTOMER COUNTER" or
   "COLLECT YOUR BARISTA WAGES") or nil)
 player:SetAttribute("RRLifeTaskName",label or
  (nextTarget and nextTarget:GetAttribute("TaskLabel") or
   (shift and "RETURN TO YOUR WORKPLACE FOR WAGES" or "")))
 player:SetAttribute("RRLifeCarTier",
  life.owned.SPORTS_CAR and "SPORTS" or
  life.owned.SEDAN and "SEDAN" or "STARTER")
end
local function venue(parent,name,pos,shade)
 local building=Instance.new("Model"); building.Name=name
 building.Parent=parent
 local floor=part(building,"Floor",Vector3.new(36,1,32),
  pos+Vector3.new(0,2,0),Color3.fromRGB(135,137,139),Enum.Material.Concrete,true)
 part(building,"Back Wall",Vector3.new(36,14,1),
  pos+Vector3.new(0,9,15),shade,Enum.Material.Brick,true)
 for _,x in ipairs({-17.5,17.5}) do
  part(building,"Side Wall",Vector3.new(1,14,32),
   pos+Vector3.new(x,9,0),shade,Enum.Material.Brick,true)
 end
 for _,x in ipairs({-11,11}) do
  part(building,"Front Wall",Vector3.new(14,14,1),
   pos+Vector3.new(x,9,-15),shade,Enum.Material.Brick,true)
 end
 part(building,"Door Frame",Vector3.new(7,3,1),
  pos+Vector3.new(0,15,-15),Color3.fromRGB(63,76,91),Enum.Material.Metal,true)
 part(building,"Roof",Vector3.new(38,1.8,34),
  pos+Vector3.new(0,17,0),Color3.fromRGB(43,53,70),Enum.Material.Slate,true)
 for _,x in ipairs({-12,12}) do
  local glass=part(building,"Shopfront Glass",Vector3.new(7,7,.3),
   pos+Vector3.new(x,8,-15.6),Color3.fromRGB(157,206,228),Enum.Material.Glass,false)
  glass.Transparency=.35
 end
 local counter=part(building,"Shop Counter",Vector3.new(13,3,3),
  pos+Vector3.new(0,4,6),Color3.fromRGB(118,95,74),Enum.Material.Wood,true)
 textSign(building,name,pos+Vector3.new(0,22,-17),Color3.fromRGB(245,229,183))
 return counter
end
local function officer(parent,id,start)
 local m=Instance.new("Model"); m.Name="AI Police Officer "..id; m.Parent=parent
 m:SetAttribute("Behavior","Patrol")
 local torso=part(m,"Police Uniform",Vector3.new(2.4,3.2,1.5),
  start,Color3.fromRGB(32,51,92),Enum.Material.Fabric,false)
 m.PrimaryPart=torso
 part(m,"Head",Vector3.new(1.6,1.6,1.6),start+Vector3.new(0,2.4,0),
  Color3.fromRGB(191,144,110),Enum.Material.SmoothPlastic,false).Shape=Enum.PartType.Ball
 part(m,"Police Cap",Vector3.new(2,.45,2),start+Vector3.new(0,3.3,0),
  Color3.fromRGB(23,32,59),Enum.Material.Fabric,false)
 for _,x in ipairs({-1.5,1.5}) do
  part(m,"Arm",Vector3.new(.7,2.7,.9),start+Vector3.new(x,-.1,0),
   Color3.fromRGB(35,53,91),Enum.Material.Fabric,false)
 end
 for _,x in ipairs({-.6,.6}) do
  part(m,"Leg",Vector3.new(.9,2.6,1),start+Vector3.new(x,-2.9,0),
   Color3.fromRGB(35,40,51),Enum.Material.Fabric,false)
 end
 local city=start.Z>1500
 local route=city and {
  start,start+Vector3.new(-26,0,-8),start+Vector3.new(-40,0,24),
  start+Vector3.new(5,0,33)
 } or {
  start,start+Vector3.new(22,0,0),start+Vector3.new(22,0,18),
  start+Vector3.new(0,0,18)
 }
 table.insert(policeUnits,{model=m,home=start,position=start,target=nil,
  started=0,route=route,routeIndex=2})
end
function Life.Build(targetWorld,options)
 context=options; world=targetWorld
 Cafe.Build(world,{
  process=function(p,kind,arg) return Life.Process(p,kind,arg) end,
  getProfile=profile,tell=tell,sync=Life.Sync,reward=context.reward
 })
 Mechanic.Build(world,{
  process=function(p,kind,arg) return Life.Process(p,kind,arg) end,
  getProfile=profile,tell=tell,sync=Life.Sync,reward=context.reward
 })
 Retail.Build(world,{
  process=function(p,kind,arg) return Life.Process(p,kind,arg) end,
  tell=tell,sync=Life.Sync,reward=context.reward
 })
 folder=Instance.new("Folder"); folder.Name="Life City Simulation"; folder.Parent=world
 Terrain:FillBlock(CFrame.new(townCenter+Vector3.new(0,-4,0)),
  Vector3.new(350,12,580),Enum.Material.Grass)
 textSign(folder,"LIFE CITY • BUILD YOUR STORY",
  townCenter+Vector3.new(0,22,-8),Color3.fromRGB(251,226,162))
 textSign(folder,"JOBS • STORES • HOMES • CREATOR STUDIO • POLICE",
  townCenter+Vector3.new(0,16,-8),Color3.fromRGB(167,224,228))
 part(folder,"Life City Boulevard",Vector3.new(320,.8,20),
  townCenter+Vector3.new(0,2.5,0),Color3.fromRGB(59,63,69),Enum.Material.Asphalt,true)
 for i=-8,8 do
  part(folder,"Boulevard Lane Marking",Vector3.new(9,.08,.6),
   townCenter+Vector3.new(i*18,3,0),Color3.fromRGB(239,218,128),
   Enum.Material.SmoothPlastic,false)
 end
 local entries={
  {"TECH","Creator Technology Store",-112,-65,Color3.fromRGB(86,127,163)},
  {"APPAREL","Clothing Boutique",-62,-65,Color3.fromRGB(150,107,157)},
  {"HOME","Home Supply Store",-12,-65,Color3.fromRGB(140,127,104)},
  {"VEHICLE","Vehicle and Marine Dealer",38,-65,Color3.fromRGB(88,137,143)},
  {"PROPERTY","Real Estate Agency",88,-65,Color3.fromRGB(122,139,103)},
  {"BUSINESS","Business Licensing Office",138,-65,Color3.fromRGB(157,127,89)},
  {"GARDEN","City Garden & Nursery",-145,-115,Color3.fromRGB(76,143,84)},
 }
 for _,entry in ipairs(entries) do
  local category,name,x,z,color=unpack(entry)
  local counter=venue(folder,name,townCenter+Vector3.new(x,0,z),color)
  stores[category]=counter
  prompt(counter,"BROWSE","Shop: "..name,function(player)
   tell(player,"OPEN LIFE SHOP • "..name.." • WALK NEAR THE COUNTER TO BUY")
  end)
 end
 -- Dedicated owner neighborhood, separate from job stations and downtown.
 Terrain:FillBlock(CFrame.new(0,-4,2785),
  Vector3.new(430,12,230),Enum.Material.Grass)
 local neighborhood=Instance.new("Folder")
 neighborhood.Name="Residential Estates Neighborhood"
 neighborhood.Parent=folder
 for _,z in ipairs({2711,2781}) do
  part(neighborhood,"Residential Asphalt Road",Vector3.new(420,.65,14),
   Vector3.new(0,2.4,z),Color3.fromRGB(59,63,68),
   Enum.Material.Asphalt,true)
  for x=-196,196,28 do
   part(neighborhood,"Neighborhood Street Lane",Vector3.new(11,.1,.45),
    Vector3.new(x,2.8,z),Color3.fromRGB(233,215,149),
    Enum.Material.Concrete,false)
  end
 end
 for i,location in ipairs(propertyBases) do
  part(neighborhood,"Home Plot "..i,Vector3.new(46,.5,51),
   location+Vector3.new(0,2.4,0),Color3.fromRGB(88,124,82),
   Enum.Material.Grass,true)
  local sign=part(neighborhood,"Property Lot Plaque "..i,Vector3.new(5,3,.4),
   location+Vector3.new(-20,5,-19),
   Color3.fromRGB(99,94,81),Enum.Material.Wood,true)
  sign:SetAttribute("LotNumber",i)
 end
 textSign(neighborhood,"RESIDENTIAL ESTATES • OWNED HOMES",
  Vector3.new(0,20,2688),Color3.fromRGB(226,232,202))
 local license=stores.BUSINESS
 prompt(license,"COLLECT REVENUE","Owned Business Earnings",function(player)
  Life.Process(player,"BusinessCollect")
 end)
 local careerCounter=venue(folder,"Career and Employment Center",
  townCenter+Vector3.new(-95,0,67),Color3.fromRGB(88,128,117))
 for i,career in ipairs(Catalog.Careers) do
  local row=math.floor((i-1)/7)
  local col=(i-1)%7
  local board=part(folder,"Career Board "..career.id,Vector3.new(4.6,4.6,1),
   careerCounter.Position+Vector3.new((col-3)*5.3,4,-12+row*8),
   Color3.fromRGB(57,83,115),Enum.Material.Metal,false)
  careerSites[career.id]=board
  prompt(board,"APPLY",career.name.." • Level "..career.level,function(player)
   Life.Process(player,"Career",career.id)
  end)
 end
 local sites={
  {"RETAIL","Retail Register",-62,69,Color3.fromRGB(110,169,133)},
  {"COURIER","Courier Dispatch",-30,69,Color3.fromRGB(118,148,181)},
  {"BARISTA","Cafe Counter",5,69,Color3.fromRGB(158,112,82)},
  {"MECHANIC","Repair Bay",42,69,Color3.fromRGB(119,133,150)},
  {"CONSTRUCTION","Construction Site",79,69,Color3.fromRGB(172,143,81)},
  {"POLICE","Police Patrol Desk",115,69,Color3.fromRGB(62,91,156)},
  {"CREATOR","Media Recording Studio",-8,24,Color3.fromRGB(145,95,160)},
  {"PARAMEDIC","Ambulance Medical Response",-123,135,Color3.fromRGB(232,228,220)},
  {"FIREFIGHTER","Fire and Rescue Station",-84,135,Color3.fromRGB(175,59,55)},
  {"CHEF","Restaurant Kitchen",-45,135,Color3.fromRGB(191,124,64)},
  {"FARMER","Greenhouse Farming",-6,135,Color3.fromRGB(88,154,91)},
  {"TEACHER","Community Classroom",33,135,Color3.fromRGB(122,145,184)},
  {"SANITATION","Recycling Depot",72,135,Color3.fromRGB(85,150,133)},
  {"ELECTRICIAN","Electrical Workshop",111,135,Color3.fromRGB(224,170,72)},
  {"PLUMBER","Plumbing Workshop",-123,184,Color3.fromRGB(93,153,197)},
  {"VETERINARIAN","Veterinary Clinic",-84,184,Color3.fromRGB(134,181,152)},
  {"REAL_ESTATE_AGENT","Property Sales Office",-45,184,Color3.fromRGB(166,143,111)},
  {"PHOTOGRAPHER","Photo Studio",-6,184,Color3.fromRGB(166,117,174)},
  {"PILOT","Flight Training Academy",33,184,Color3.fromRGB(91,133,174)},
  {"MUSICIAN","Recording and Rehearsal",72,184,Color3.fromRGB(179,99,141)},
 }
 local added=0
 for _,career in ipairs(Catalog.Careers) do
  if Catalog.CareerTasks[career.id] then
   added+=1
   local col=(added-1)%10
   local row=math.floor((added-1)/10)
   table.insert(sites,{career.id,career.name.." Workstation",
    -146+col*32,232+row*38,Color3.fromRGB(96,128,143)})
  end
 end
 Terrain:FillBlock(CFrame.new(townCenter+Vector3.new(0,-4,315)),
  Vector3.new(340,12,360),Enum.Material.Grass)
 for _,entry in ipairs(sites) do
  local id,name,x,z,color=unpack(entry)
  local node=part(folder,name,Vector3.new(8,5,5),
   townCenter+Vector3.new(x,5,z),color,Enum.Material.Metal,true)
  node:SetAttribute("CareerSite",id)
  workSites[id]=node
  prompt(node,id=="CREATOR" and "RECORD VIDEO" or "WORK SHIFT",name,
   function(player) Life.Process(player,id=="CREATOR" and "Publish" or "Work",id) end)
  textSign(folder,name,node.Position+Vector3.new(0,9,0),color)
  if id~="CREATOR" then
   local steps={
    RETAIL={"SCAN CUSTOMER ITEMS","STOCK DISPLAY SHELF"},
    COURIER={"PICK UP PARCEL","DELIVER TO CUSTOMER"},
    BARISTA={"PREPARE COFFEE ORDER","SERVE CUSTOMER"},
    MECHANIC={"INSPECT ENGINE","REPLACE WORN PART"},
    CONSTRUCTION={"MEASURE BUILD SITE","INSTALL BUILDING MATERIAL"},
    POLICE={"CHECK INCIDENT REPORT","INTERVIEW WITNESS"},
    PARAMEDIC={"CHECK PATIENT VITALS","APPLY FIRST AID"},
    FIREFIGHTER={"CHECK FIRE HOSE","EXTINGUISH TRAINING FIRE"},
    CHEF={"PREPARE INGREDIENTS","PLATE THE MEAL"},
    FARMER={"PLANT SEEDLINGS","HARVEST CROPS"},
    TEACHER={"PREPARE LESSON","TEACH CLASS"},
    SANITATION={"COLLECT RECYCLABLES","SORT WASTE"},
    ELECTRICIAN={"INSPECT CIRCUIT","RESTORE POWER"},
    PLUMBER={"INSPECT LEAK","REPAIR PIPE"},
    VETERINARIAN={"EXAMINE PET","ADMINISTER CARE"},
    REAL_ESTATE_AGENT={"STAGE PROPERTY","SHOW HOME TO CLIENT"},
    PHOTOGRAPHER={"SET UP LIGHTS","TAKE PORTRAIT"},
    PILOT={"RUN PRE-FLIGHT CHECK","CONFIRM LANDING PROCEDURE"},
    MUSICIAN={"TUNE INSTRUMENT","PERFORM ON STAGE"},
   }
   local actions=steps[id] or Catalog.CareerTasks[id]
   taskSites[id]={}
   for step=1,2 do
    local pos=node.Position+Vector3.new(step==1 and -12 or 12,-.4,9)
    local target=part(folder,"Job Task "..id.." "..step,
     Vector3.new(6,3,4),pos,
     step==1 and Color3.fromRGB(116,169,190) or
     Color3.fromRGB(184,141,94),Enum.Material.Metal,true)
    target:SetAttribute("Job",id); target:SetAttribute("Step",step)
    target:SetAttribute("TaskLabel",actions[step])
    taskSites[id][step]=target
    textSign(folder,actions[step],pos+Vector3.new(0,6,0),
     Color3.fromRGB(255,240,187))
    prompt(target,actions[step],name,function(player)
     Life.Process(player,"Task",id,step)
    end)
   end
  end
 end
 local jail=Instance.new("Model"); jail.Name="Life City Jail"; jail.Parent=folder
 part(jail,"Jail Floor",Vector3.new(38,1,38),
  jailCenter-Vector3.new(0,4,0),Color3.fromRGB(100,109,119),Enum.Material.Concrete,true)
 for _,z in ipairs({-19,19}) do
  part(jail,"Jail Wall",Vector3.new(38,16,1),
   jailCenter+Vector3.new(0,3,z),Color3.fromRGB(98,111,127),Enum.Material.Concrete,true)
 end
 for _,x in ipairs({-19,19}) do
  part(jail,"Jail Wall",Vector3.new(1,16,38),
   jailCenter+Vector3.new(x,3,0),Color3.fromRGB(98,111,127),Enum.Material.Concrete,true)
 end
 for i=-3,3 do
  part(jail,"Cell Bars",Vector3.new(.55,12,.55),
   jailCenter+Vector3.new(i*3,3,-17.8),Color3.fromRGB(57,65,78),Enum.Material.Metal,true)
 end
 textSign(jail,"POLICE • JAIL • FINES",jailCenter+Vector3.new(0,17,0),
  Color3.fromRGB(254,188,126))
 local fines=part(folder,"Fine Payment Counter",Vector3.new(6,4,4),
  townCenter+Vector3.new(125,5,26),Color3.fromRGB(109,144,179),Enum.Material.Metal,true)
 fineCounter=fines
 prompt(fines,"PAY FINE","Life City Court",function(player)
  Life.Process(player,"PayFine")
 end)
 local meal=part(folder,"Community Meal Station",Vector3.new(8,4,5),
  townCenter+Vector3.new(-50,5,114),
  Color3.fromRGB(156,126,88),Enum.Material.Wood,true)
 foodCounter=meal
 textSign(folder,"COMMUNITY KITCHEN • MEALS",
  meal.Position+Vector3.new(0,8,0),Color3.fromRGB(241,223,176))
 prompt(meal,"EAT MEAL","Community Kitchen",function(player)
  Life.Process(player,"Eat","COMMUNITY")
 end)
 local bench=part(folder,"Public Rest Bench",Vector3.new(9,2,4),
  townCenter+Vector3.new(20,4,115),
  Color3.fromRGB(121,95,74),Enum.Material.Wood,true)
 restCounter=bench
 prompt(bench,"REST","Public Park Bench",function(player)
  Life.Process(player,"Rest","PUBLIC")
 end)
 policeUnits={}
 officer(folder,1,Vector3.new(180,7,18))
 officer(folder,2,townCenter+Vector3.new(113,7,23))
 return townCenter+Vector3.new(0,7,0)
end
-- Connect the life simulation to the imported official Modern City art.
-- These are intentionally tiny/invisible interaction anchors around real mesh
-- buildings; we do not build another fake city out of primitive cubes.
function Life.AttachDowntown(cityModel)
 if not folder or not cityModel or not cityModel.Parent then return false end
 local old=folder:FindFirstChild("Modern Downtown Life Services")
 if old then old:Destroy() end
 local services=Instance.new("Folder")
 services.Name="Modern Downtown Life Services"
 services.Parent=folder
 local function anchor(name,pos,visible)
  local node=part(services,name,Vector3.new(4.5,3,.5),pos,
   Color3.fromRGB(37,47,56),Enum.Material.Metal,false)
  node.Transparency=visible and .08 or 1
  node.CanQuery=true
  return node
 end
 local function plaque(name,pos,title,subtitle,color)
  local node=anchor(name,pos,true)
  node.Size=Vector3.new(7,4,.45)
  node.Color=color or Color3.fromRGB(39,54,64)
  local gui=Instance.new("SurfaceGui")
  gui.Name="Downtown Business Sign"
  gui.Face=Enum.NormalId.Front
  gui.CanvasSize=Vector2.new(700,400)
  gui.LightInfluence=.25
  gui.Parent=node
  local main=Instance.new("TextLabel")
  main.Size=UDim2.new(.94,0,.55,0); main.Position=UDim2.new(.03,0,.04,0)
  main.BackgroundTransparency=1; main.Text=title; main.TextWrapped=true
  main.TextScaled=true; main.Font=Enum.Font.GothamBold
  main.TextColor3=Color3.fromRGB(244,237,213); main.Parent=gui
  local sub=Instance.new("TextLabel")
  sub.Size=UDim2.new(.94,0,.27,0); sub.Position=UDim2.new(.03,0,.66,0)
  sub.BackgroundTransparency=1; sub.Text=subtitle; sub.TextWrapped=true
  sub.TextScaled=true; sub.Font=Enum.Font.Gotham
  sub.TextColor3=Color3.fromRGB(151,208,220); sub.Parent=gui
  return node
 end
 -- One clean employment office replaces 20 giant floating career boards.
 local employment=plaque("Downtown Employment Center",Vector3.new(-73,5,2247),
  "CITY EMPLOYMENT","60 CAREERS • APPLY IN LIFE MENU",Color3.fromRGB(47,78,82))
 prompt(employment,"BROWSE JOBS","Downtown Employment Center",function(player)
  tell(player,"OPEN LIFE • CHOOSE ANY CAREER YOU QUALIFY FOR • APPLY HERE")
 end)
 for _,career in ipairs(Catalog.Careers) do downtownCareerSites[career.id]=employment end
 -- Real storefront row. Shopping stays server-validated and paid with earned coins.
 local storefronts={
  {"APPAREL",-50,"THREADS","CLOTHING & FOOTWEAR"},
  {"TECH",-28,"CITY TECH","PHONES • COMPUTERS • CREATOR GEAR"},
  {"HOME",-6,"HOME & MORE","FURNITURE • TOOLS • GROCERIES"},
  {"VEHICLE",18,"MOTOR ROW","CARS • BIKES • BOATS"},
  {"PROPERTY",42,"METRO REALTY","APARTMENTS • HOMES • LAND"},
  {"BUSINESS",68,"CITY COMMERCE","BUY & RUN BUSINESSES"},
  {"GARDEN",77,"GARDEN NURSERY","SEEDS • TOOLS • LANDSCAPING"},
 }
 for _,entry in ipairs(storefronts) do
  local category,x,title,subtitle=unpack(entry)
  local node=plaque("Downtown Store "..category,
   Vector3.new(x,5,category=="GARDEN" and 2185 or 2247),
   title,subtitle,Color3.fromRGB(50,61,72))
  downtownStores[category]=node
  prompt(node,"SHOP",title,function(player)
   tell(player,"OPEN LIFE SHOP • "..title.." • PURCHASES USE EARNED IN-GAME COINS")
  end)
 end
 prompt(downtownStores.BUSINESS,"COLLECT REVENUE","Your Downtown Businesses",function(player)
  Life.Process(player,"BusinessCollect")
 end)
 -- Workplaces are spread around the actual imported city block. Invisible
 -- anchors preserve the official mesh art; prompts identify the real activity.
 local jobPositions={
  RETAIL=Vector3.new(-72,3,2263), BARISTA=Vector3.new(-36,3,2263),
  CREATOR=Vector3.new(0,3,2263), COURIER=Vector3.new(36,3,2263),
  MECHANIC=Vector3.new(72,3,2263),
  PARAMEDIC=Vector3.new(-100,3,2300), FIREFIGHTER=Vector3.new(-100,3,2340),
  CHEF=Vector3.new(-100,3,2380), FARMER=Vector3.new(-100,3,2420),
  CONSTRUCTION=Vector3.new(-100,3,2460),
  POLICE=Vector3.new(100,3,2300), TEACHER=Vector3.new(100,3,2340),
  SANITATION=Vector3.new(100,3,2380), ELECTRICIAN=Vector3.new(100,3,2420),
  PLUMBER=Vector3.new(100,3,2460),
  VETERINARIAN=Vector3.new(-70,3,2480), REAL_ESTATE_AGENT=Vector3.new(-35,3,2480),
  PHOTOGRAPHER=Vector3.new(0,3,2480), PILOT=Vector3.new(35,3,2480),
  MUSICIAN=Vector3.new(70,3,2480),
 }
 local taskLabels={
  RETAIL={"SCAN CUSTOMER ITEMS","STOCK DISPLAY SHELF"},
  COURIER={"PICK UP PARCEL","DELIVER TO CUSTOMER"},
  BARISTA={"PREPARE COFFEE ORDER","SERVE CUSTOMER"},
  MECHANIC={"INSPECT ENGINE","REPLACE WORN PART"},
  CONSTRUCTION={"MEASURE BUILD SITE","INSTALL BUILDING MATERIAL"},
  POLICE={"CHECK INCIDENT REPORT","INTERVIEW WITNESS"},
  PARAMEDIC={"CHECK PATIENT VITALS","APPLY FIRST AID"},
  FIREFIGHTER={"CHECK FIRE HOSE","EXTINGUISH TRAINING FIRE"},
  CHEF={"PREPARE INGREDIENTS","PLATE THE MEAL"},
  FARMER={"PLANT SEEDLINGS","HARVEST CROPS"},
  TEACHER={"PREPARE LESSON","TEACH CLASS"},
  SANITATION={"COLLECT RECYCLABLES","SORT WASTE"},
  ELECTRICIAN={"INSPECT CIRCUIT","RESTORE POWER"},
  PLUMBER={"INSPECT LEAK","REPAIR PIPE"},
  VETERINARIAN={"EXAMINE PET","ADMINISTER CARE"},
  REAL_ESTATE_AGENT={"STAGE PROPERTY","SHOW HOME TO CLIENT"},
  PHOTOGRAPHER={"SET UP LIGHTS","TAKE PORTRAIT"},
  PILOT={"RUN PRE-FLIGHT CHECK","CONFIRM LANDING PROCEDURE"},
  MUSICIAN={"TUNE INSTRUMENT","PERFORM ON STAGE"},
 }
 local addedCareers=0
 for _,career in ipairs(Catalog.Careers) do
  local pos=jobPositions[career.id]
  if not pos then
   addedCareers+=1
   local row=math.floor((addedCareers-1)/2)
   local side=addedCareers%2==1 and -1 or 1
   pos=Vector3.new(side*140,3,2192+row*17)
  end
  if pos then
   local site=anchor("Downtown Worksite "..career.id,pos,false)
   site:SetAttribute("CareerSite",career.id)
   downtownWorkSites[career.id]=site
   if Catalog.CareerTasks[career.id] then
    local note=plaque("Work Sign "..career.id,pos+Vector3.new(0,5,0),
     career.name:upper(),"START SHIFT • COMPLETE 2 TASKS",
     Color3.fromRGB(59,93,106))
    note.CanCollide=false
   end
   prompt(site,career.id=="CREATOR" and "RECORD VIDEO" or "WORK SHIFT",
    career.name,function(player)
     Life.Process(player,career.id=="CREATOR" and "Publish" or "Work",career.id)
    end)
   if career.id~="CREATOR" then
    downtownTaskSites[career.id]={}
    local labels=taskLabels[career.id] or Catalog.CareerTasks[career.id]
    local tangent=(math.abs(pos.X)>90) and Vector3.new(0,0,8) or Vector3.new(8,0,0)
    for step=1,2 do
     local taskPos=pos+tangent*(step==1 and -1 or 1)
     local target=anchor("Downtown Job Task "..career.id.." "..step,taskPos,false)
     target:SetAttribute("Job",career.id); target:SetAttribute("Step",step)
     target:SetAttribute("TaskLabel",labels[step])
     downtownTaskSites[career.id][step]=target
     prompt(target,labels[step],career.name,function(player)
      Life.Process(player,"Task",career.id,step)
     end)
    end
   end
  end
 end
 -- Civic services integrated into the same walkable downtown block.
 downtownFineCounter=plaque("Downtown Court Payments",Vector3.new(88,5,2282),
  "CITY COURT","PAY FINES",Color3.fromRGB(66,76,91))
 prompt(downtownFineCounter,"PAY FINE","Downtown Court",function(player)
  Life.Process(player,"PayFine")
 end)
 downtownFoodCounter=anchor("Downtown Community Meal",Vector3.new(-88,3,2282),false)
 prompt(downtownFoodCounter,"EAT MEAL","Community Food Pantry",function(player)
  Life.Process(player,"Eat","COMMUNITY")
 end)
 downtownRestCounter=anchor("Downtown Public Rest",Vector3.new(0,3,2228),false)
 prompt(downtownRestCounter,"REST","Downtown Public Bench",function(player)
  Life.Process(player,"Rest","PUBLIC")
 end)
 -- Players can own and tend individual garden beds within walking distance.
 Garden.Build(world,{
  process=function(p,kind,arg) return Life.Process(p,kind,arg) end,
  getProfile=profile,tell=tell,sync=Life.Sync,reward=context.reward
 })
 -- Reuse genuine official Modern City tree meshes to landscape the estates.
 -- All source assets were stripped of executable scripts before import.
 local estate=folder:FindFirstChild("Residential Estates Neighborhood")
 local streetTrees=cityModel:FindFirstChild("StreetTrees",true)
 if estate and streetTrees then
  local source=streetTrees:GetChildren()
  local placed=0
  for row=0,1 do
   for i=1,6 do
    local tree=source[((i-1)%#source)+1]
    if tree and tree:IsA("Model") then
     local clone=tree:Clone()
     clone.Name="Official Estate Mesh Tree "..(row*6+i)
     clone.Parent=estate
     local cf,size=clone:GetBoundingBox()
     local target=Vector3.new(-186+(i-1)*73,2.6,2738+row*70)
     local bottom=cf.Position.Y-size.Y*.5
     clone:PivotTo(clone:GetPivot()+Vector3.new(
      target.X-cf.Position.X,target.Y-bottom,target.Z-cf.Position.Z))
     for _,part in ipairs(clone:GetDescendants()) do
      if part:IsA("BasePart") then
       part.Anchored=true
       part.CanTouch=false
       part.CanCollide=false
      end
     end
     placed+=1
    end
   end
  end
  estate:SetAttribute("OfficialMeshTrees",placed)
 end
 -- Two additional officers make the detailed district participate in the law system.
 officer(services,3,Vector3.new(-92,7,2295))
 officer(services,4,Vector3.new(92,7,2395))
 cityModel:SetAttribute("LifeSimulationIntegrated",true)
 cityModel:SetAttribute("DowntownCareerCount",#Catalog.Careers)
 return true
end

function Life.RefreshProperty(player)
 local s=profile(player)
 if not s or not s.life then return end
 local owned=s.life.owned
 local priority={
  "PRIVATE_ISLAND","VILLA","PENTHOUSE","MANSION","BEACH_HOUSE",
  "FARMHOUSE","LAKE_CABIN","TOWNHOUSE","STARTER_HOME",
  "CONDO","APARTMENT",
 }
 local tier=nil
 for _,candidate in ipairs(priority) do
  if owned[candidate] then tier=candidate;break end
 end
 local old=playerProperties[player]
 if old then old:Destroy(); playerProperties[player]=nil end
 if not tier then return end
 local slot=playerSlots[player]
 if not slot then return end
 local center=propertyBases[slot]
 local m=Instance.new("Model")
 m.Name="Owned "..tier.." "..player.UserId
 m:SetAttribute("OwnerUserId",player.UserId)
 m:SetAttribute("PropertyTier",tier)
 m.Parent=folder
 playerProperties[player]=m
 local luxury={PRIVATE_ISLAND=true,VILLA=true,PENTHOUSE=true,MANSION=true}
 local middle={BEACH_HOUSE=true,FARMHOUSE=true,LAKE_CABIN=true,
  TOWNHOUSE=true,STARTER_HOME=true}
 local width=luxury[tier] and 36 or middle[tier] and 29 or 24
 local floors=luxury[tier] and 3 or middle[tier] and 2 or 1
 local height=floors*10
 local color=luxury[tier] and Color3.fromRGB(216,211,199) or
  middle[tier] and Color3.fromRGB(183,143,115) or
  Color3.fromRGB(173,181,190)
 part(m,"Property Foundation",Vector3.new(width+3,1,30),
  center+Vector3.new(0,3,0),Color3.fromRGB(132,134,132),Enum.Material.Concrete,true)
 -- Walkable ground floor: four actual walls with an open doorway, not a solid cube.
 for _,x in ipairs({-width*.5,width*.5}) do
  part(m,"Property Side Wall",Vector3.new(1,height,26),
   center+Vector3.new(x,3+height*.5,0),color,Enum.Material.Brick,true)
 end
 part(m,"Property Rear Wall",Vector3.new(width,height,1),
  center+Vector3.new(0,3+height*.5,13),color,Enum.Material.Brick,true)
 for _,x in ipairs({-1,1}) do
  part(m,"Property Front Wall",Vector3.new((width-7)*.5,height,1),
   center+Vector3.new(x*(width+7)*.25,3+height*.5,-13),
   color,Enum.Material.Brick,true)
 end
 -- A player can enter, walk to furniture, and use the sofa/bed.
 local interior=Color3.fromRGB(204,194,175)
 part(m,"Interior Wood Floor",Vector3.new(width-2,.25,25),
  center+Vector3.new(0,3.65,0),Color3.fromRGB(145,105,77),
  Enum.Material.WoodPlanks,true)
 for _,x in ipairs({-width*.5+1,width*.5-1}) do
  part(m,"Interior Baseboard",Vector3.new(.2,.5,24),
   center+Vector3.new(x,4,0),interior,Enum.Material.Wood,false)
 end
 part(m,"Living Room Rug",Vector3.new(10,.1,7),
  center+Vector3.new(-width*.23,3.9,-2),
  Color3.fromRGB(122,137,148),Enum.Material.Fabric,false)
 part(m,"Sofa Seat",Vector3.new(7,1.3,3),
  center+Vector3.new(-width*.25,5,-2),
  Color3.fromRGB(94,123,127),Enum.Material.Fabric,true)
 part(m,"Sofa Back",Vector3.new(7,2.5,.9),
  center+Vector3.new(-width*.25,6,-.4),
  Color3.fromRGB(94,123,127),Enum.Material.Fabric,true)
 part(m,"Coffee Table",Vector3.new(5,.6,2.8),
  center+Vector3.new(-width*.25,4.7,-7),
  Color3.fromRGB(125,92,65),Enum.Material.Wood,true)
 part(m,"Bed Frame",Vector3.new(7,1,9),
  center+Vector3.new(width*.25,4.5,4),
  Color3.fromRGB(111,91,79),Enum.Material.Wood,true)
 part(m,"Bed Mattress",Vector3.new(6.6,.6,8.4),
  center+Vector3.new(width*.25,5.2,4),
  Color3.fromRGB(229,224,214),Enum.Material.Fabric,true)
 part(m,"Bed Pillow",Vector3.new(4,.5,1.8),
  center+Vector3.new(width*.25,5.8,7),
  Color3.fromRGB(243,241,230),Enum.Material.Fabric,false)
 part(m,"Kitchen Counter",Vector3.new(9,3,2.5),
  center+Vector3.new(-width*.25,5.3,9),
  Color3.fromRGB(159,160,154),Enum.Material.Marble,true)
 local kitchen=part(m,"Kitchen Sink",Vector3.new(2.2,.15,1.7),
  center+Vector3.new(-width*.25,6.9,8.9),
  Color3.fromRGB(91,104,110),Enum.Material.Metal,false)
 local sinkPrompt=Instance.new("ProximityPrompt")
 sinkPrompt.ActionText="WASH UP"; sinkPrompt.ObjectText="Home Kitchen"
 sinkPrompt.MaxActivationDistance=10; sinkPrompt.Parent=kitchen
 sinkPrompt.Triggered:Connect(function(p)
  if p==player then
   local state=profile(p)
   if state and state.life then
    state.life.needs.hygiene=100
    Life.Sync(p)
    tell(p,"SHOWERED AND FRESHENED UP • HYGIENE 100!")
   end
  end
 end)
 local bed=part(m,"Bed Interaction",Vector3.new(2,.2,2),
  center+Vector3.new(width*.25,6,4),
  Color3.fromRGB(229,224,214),Enum.Material.Fabric,false)
 bed.Transparency=1
 local restPrompt=Instance.new("ProximityPrompt")
 restPrompt.ActionText="REST"; restPrompt.ObjectText="Your Home"
 restPrompt.MaxActivationDistance=11; restPrompt.Parent=bed
 restPrompt.Triggered:Connect(function(p)
  if p==player then
   local state=profile(p)
   if state and state.life then
    state.life.needs.energy=100
    Life.Sync(p)
    tell(p,"SLEPT IN YOUR OWN BED • ENERGY 100!")
   end
  end
 end)
 -- Open stairwell and upstairs rooms are created by HomeArchitecture.Build.
 -- Gabled two-slope roof with overhang, ridge, chimney and front porch.
 for _,side in ipairs({-1,1}) do
  local wedge=Instance.new("WedgePart")
  wedge.Name="Sloped Architectural Roof"
  wedge.Size=Vector3.new(29,5,(width+3)*.5)
  wedge.CFrame=CFrame.new(center+Vector3.new(
   side*(width+3)*.25,6.5+height,0))*
   CFrame.Angles(0,side==1 and math.pi*.5 or -math.pi*.5,0)
  wedge.Anchored=true; wedge.CanCollide=true
  wedge.Material=Enum.Material.Slate
  wedge.Color=Color3.fromRGB(62,71,82); wedge.Parent=m
 end
 part(m,"Roof Ridge Cap",Vector3.new(1,1.1,31),
  center+Vector3.new(0,9.2+height,0),
  Color3.fromRGB(57,63,73),Enum.Material.Metal,false)
 part(m,"Brick Chimney",Vector3.new(3,7,3),
  center+Vector3.new(width*.29,9+height,5),
  Color3.fromRGB(151,101,91),Enum.Material.Brick,true)
 part(m,"Front Porch",Vector3.new(12,.7,7),
  center+Vector3.new(0,3.4,-17),
  Color3.fromRGB(173,167,155),Enum.Material.Concrete,true)
 for _,x in ipairs({-5,5}) do
  local column=part(m,"Porch Column",Vector3.new(1.2,9,1.2),
   center+Vector3.new(x,8,-19),
   Color3.fromRGB(226,222,207),Enum.Material.Limestone,true)
  column.Shape=Enum.PartType.Cylinder
 end
 part(m,"Porch Overhang",Vector3.new(13,.8,7),
  center+Vector3.new(0,12.8,-17),
  Color3.fromRGB(65,75,85),Enum.Material.Slate,true)
 for _,z in ipairs({-21,-23}) do
  part(m,"Front Steps",Vector3.new(9,.55,2),
   center+Vector3.new(0,z==-21 and 2.7 or 2.2,z),
   Color3.fromRGB(165,162,152),Enum.Material.Concrete,true)
 end
 part(m,"Home Driveway",Vector3.new(11,.3,20),
  center+Vector3.new(width*.28,2.2,-25),
  Color3.fromRGB(151,153,150),Enum.Material.Concrete,true)
 for _,x in ipairs({-width*.5+3,width*.5-3}) do
  local shrub=part(m,"Front Garden Shrub",Vector3.new(4,3,4),
   center+Vector3.new(x,4,-17),
   Color3.fromRGB(68,123,75),Enum.Material.Grass,false)
  shrub.Shape=Enum.PartType.Ball
 end
 local houseLight=part(m,"Porch Light",Vector3.new(1.3,1.3,1.3),
  center+Vector3.new(0,10.8,-13.5),
  Color3.fromRGB(252,224,175),Enum.Material.Neon,false)
 local bulb=Instance.new("PointLight"); bulb.Brightness=.8; bulb.Range=12
 bulb.Color=Color3.fromRGB(255,223,175); bulb.Parent=houseLight
 for floorIndex=1,floors do
  for _,x in ipairs({-width*.28,width*.28}) do
   for _,z in ipairs({-13.2,13.2}) do
    local glass=part(m,"Property Window",Vector3.new(5,5,.25),
     center+Vector3.new(x,5+floorIndex*9-5,z),
     Color3.fromRGB(115,182,210),Enum.Material.Glass,false)
    glass.Transparency=.23
   end
  end
 end
 local originalDoor=part(m,"Property Entrance",Vector3.new(6,8,.5),
  center+Vector3.new(0,7,-13.5),
  Color3.fromRGB(76,92,108),Enum.Material.WoodPlanks,false)
 originalDoor.Transparency=1
 textSign(m,tier.." • "..player.DisplayName,
  center+Vector3.new(0,height+12,-15),Color3.fromRGB(255,235,169))
 local homeContext={getProfile=profile,tell=tell,sync=Life.Sync}
 Architecture.Build(m,center,width,floors,tier,player,owned,homeContext)
 Home.Furnish(m,center,width,floors,player,owned,homeContext)
end
function Life.PlayerJoined(player)
 if playerSlots[player] then return end
 for i=1,#propertyBases do
  if not propertySlots[i] then
   propertySlots[i]=player; playerSlots[player]=i
   break
  end
 end
 Life.RefreshProperty(player)
 Garden.PlayerJoined(player)
end
function Life.PlayerRemoving(player)
 local slot=playerSlots[player]
 if slot then propertySlots[slot]=nil end
 playerSlots[player]=nil
 local m=playerProperties[player]
 if m then m:Destroy() end
 playerProperties[player]=nil
 lastAction[player]=nil
 publicMealCooldown[player]=nil
 Garden.PlayerRemoving(player)
end
function Life.GiveCamera(player)
 local s=profile(player)
 if not s or not s.life then return end
 Garden.GiveTools(player,s.life)
 if not s.life.owned.CAMERA then return end
 local backpack=player:FindFirstChildOfClass("Backpack")
 if not backpack then return end
 if backpack:FindFirstChild("Creator Camera") or
  (player.Character and player.Character:FindFirstChild("Creator Camera")) then return end
 local tool=Instance.new("Tool"); tool.Name="Creator Camera"
 tool.ToolTip="Equip at the Life City recording studio, then tap RECORD"
 tool.CanBeDropped=false; tool.RequiresHandle=true
 local handle=Instance.new("Part"); handle.Name="Handle"
 handle.Size=Vector3.new(2,1.4,1.3)
 handle.Material=Enum.Material.Metal; handle.Color=Color3.fromRGB(42,48,58)
 handle.CanCollide=false; handle.Massless=true; handle.Parent=tool
 local lens=Instance.new("Part"); lens.Name="Camera Lens"
 lens.Shape=Enum.PartType.Cylinder
 lens.Size=Vector3.new(.85,1.1,1.1)
 lens.Color=Color3.fromRGB(90,158,188)
 lens.Material=Enum.Material.Glass; lens.CanCollide=false; lens.Massless=true
 lens.CFrame=handle.CFrame*CFrame.new(0,0,-.85)*CFrame.Angles(0,0,math.rad(90))
 lens.Parent=tool
 local weld=Instance.new("WeldConstraint"); weld.Part0=handle
 weld.Part1=lens; weld.Parent=handle
 tool.Parent=backpack
end
function Life.IsJailed(player)
 local s=profile(player)
 return s and s.life and os.clock()<s.life.jailUntil or false
end
function Life.Process(player,kind,arg,step)
 local s=profile(player)
 if not s or not s.life or type(kind)~="string" then return false end
 local life=s.life
 if Life.IsJailed(player) then
  tell(player,"YOU ARE SERVING A SHORT IN-GAME JAIL SENTENCE.")
  return false
 end
 local now=os.clock()
 if now-(lastAction[player] or -100)<.35 then return false end
 lastAction[player]=now
 if kind=="Career" then
  local career=type(arg)=="string" and Catalog.CareerById[arg]
  if not career or not nearCareer(player,arg,17) then return false end
  if s.level<career.level then
   tell(player,"REACH LEVEL "..career.level.." TO APPLY."); return false
  end
  if s.heat>0 then tell(player,"CLEAR YOUR WANTED HEAT BEFORE APPLYING."); return false end
  life.career=arg
  life.activeShift=nil
  tell(player,"HIRED: "..career.name.."! FIND YOUR WORKPLACE.")
 elseif kind=="Work" then
  local career=type(arg)=="string" and Catalog.CareerById[arg]
  if not career or arg=="CREATOR" or life.career~=arg or
   not nearWork(player,arg,18) then return false end
  if life.needs.energy<10 or life.needs.hunger<10 then
   tell(player,"TOO TIRED OR HUNGRY TO WORK • REST OR EAT AT THE COMMUNITY KITCHEN.")
   return false
  end
  if now-life.lastWork<12 then
   tell(player,"SHIFT REST BREAK • TRY AGAIN SHORTLY."); return false
  end
  if arg=="POLICE" and s.heat>0 then
   tell(player,"POLICE OFFICERS MUST HAVE A CLEAR RECORD."); return false
  end
  if not life.activeShift or life.activeShift.id~=arg then
   life.activeShift={id=arg,started=now,progress=0,taskAt=0}
   if arg=="BARISTA" then
    local coffee=Cafe.Assign(life.activeShift)
    tell(player,"CUSTOMER WANTS "..coffee..
     "! VISIT THE BEAN & BREW MACHINE NEAR THE DOWNTOWN BARISTA WORKSITE.")
   elseif arg=="RETAIL" and nearby(player,downtownWorkSites.RETAIL,18) then
    local scan,stock=Retail.Assign(life.activeShift)
    tell(player,"NEW CUSTOMER ORDER: SCAN "..scan.." AT THE CORNER MARKET, THEN RESTOCK "..stock.." ON ITS SHELF.")
   elseif arg=="MECHANIC" then
    Mechanic.Assign(life.activeShift)
    tell(player,"NEW VEHICLE IN THE SERVICE BAY! INSPECT IT AT THE PIT STOP DIAGNOSTIC TABLET NEAR MOTOR ROW.")
   else
    tell(player,"SHIFT STARTED: "..career.name..
     " • COMPLETE THE TWO WORK TASKS MARKED NEARBY.")
   end
   Life.Sync(player)
   return true
  end
  if life.activeShift.progress<2 then
   tell(player,"COMPLETE BOTH WORK TASKS BEFORE COLLECTING YOUR WAGES.")
   return false
  end
  life.activeShift=nil
  life.lastWork=now; life.shifts+=1
  life.needs.energy=math.max(0,life.needs.energy-5)
  life.needs.hunger=math.max(0,life.needs.hunger-4)
  life.needs.hygiene=math.max(0,life.needs.hygiene-2)
  life.reputation=math.min(1000000,life.reputation+1)
  context.reward(player,career.wage,14,0)
  if context.onActivity then context.onActivity(player,"SHIFT",arg) end
  tell(player,"SHIFT COMPLETED! +"..career.wage.." COINS • +14 XP")
 elseif kind=="CafeBrew" or kind=="CafeServe" then
  return Cafe.Process(player,kind,arg,life.activeShift)
 elseif kind=="MechanicInspect" or kind=="MechanicRepair" then
  return Mechanic.Process(player,kind,arg,life.activeShift)
 elseif kind=="RetailScan" or kind=="RetailStock" then
  return Retail.Process(player,kind,arg,life.activeShift)
 elseif kind=="Task" then
  if arg=="RETAIL" and life.activeShift and life.activeShift.retailScanSku then
   tell(player,"DOWNTOWN RETAIL WORKERS MUST SCAN THE REAL CUSTOMER ITEM AND RESTOCK THE LABELED SHELF.")
   return false
  end
  if arg=="MECHANIC" then
   tell(player,"MECHANICS MUST INSPECT THE DEMO CAR AND REPAIR THE ACTUAL FAULT AT THE PIT STOP.")
   return false
  end
  if arg=="BARISTA" then
   tell(player,"BARISTAS MUST BREW THE CUSTOMER'S ACTUAL DRINK AND SERVE IT AT THE BEAN & BREW.")
   return false
  end
  local shift=life.activeShift
  if type(arg)~="string" or not Catalog.CareerById[arg] or
   not shift or shift.id~=arg or life.career~=arg then return false end
  local expected=shift.progress+1
  if type(step)~="number" or step~=expected or step>2 or
   not nearTask(player,arg,step,15) then
   tell(player,"FOLLOW YOUR ASSIGNED WORK TASKS IN ORDER.")
   return false
  end
  if now-shift.started<1.5 or
   (shift.progress>0 and now-shift.taskAt<1.5) then
   tell(player,"TAKE TIME TO COMPLETE YOUR WORK SAFELY.")
   return false
  end
  if arg=="PHOTOGRAPHER" and not life.owned.CAMERA then
   tell(player,"PHOTOGRAPHERS NEED A CAMERA FROM THE TECH STORE.")
   return false
  end
  if arg=="MUSICIAN" and not life.owned.GUITAR then
   tell(player,"MUSICIANS NEED A GUITAR FROM THE TECH STORE.")
   return false
  end
  shift.progress=step; shift.taskAt=now
  tell(player,step==2 and "ALL TASKS DONE! RETURN TO THE WORK STATION FOR WAGES."
   or "FIRST TASK COMPLETE! FIND THE SECOND WORK TASK.")
  Life.Sync(player)
  return true
 elseif kind=="Eat" then
  if arg~="COMMUNITY" or not nearbyEither(player,foodCounter,downtownFoodCounter,17) then return false end
  if now-(publicMealCooldown[player] or -1000)<45 then
   tell(player,"THE KITCHEN IS PREPARING MORE MEALS • COME BACK SOON.")
   return false
  end
  publicMealCooldown[player]=now
  life.needs.hunger=math.min(100,life.needs.hunger+50)
  tell(player,"ATE A FREE COMMUNITY MEAL • HUNGER RESTORED!")
 elseif kind=="Rest" then
  if arg~="PUBLIC" or not
   (nearbyEither(player,restCounter,downtownRestCounter,17) or
   registeredNearby(player,externalRestSites,"PUBLIC",17)) then return false end
  life.needs.energy=math.min(100,life.needs.energy+25)
  tell(player,"RESTED AT THE PARK • ENERGY RESTORED!")
 elseif kind=="BuySnack" then
  if arg~="MARKET" or not registeredNearby(player,
   externalSnackSites,"MARKET",16) then
   return false
  end
  if s.coins<15 then
   tell(player,"YOU NEED 15 EARNED COINS FOR A MARKET SNACK.")
   return false
  end
  if life.needs.hunger>=95 then
   tell(player,"YOU ARE ALREADY FULL!")
   return false
  end
  local time=os.clock()
  if time-(life.lastSnack or -100)>25 then
   life.lastSnack=time
   s.coins-=15
   life.needs.hunger=math.min(100,life.needs.hunger+35)
   tell(player,"BOUGHT A MARKET SNACK FOR 15 COINS • HUNGER +35.")
  else
   tell(player,"WAIT A LITTLE BEFORE EATING ANOTHER SNACK.")
   return false
  end
 elseif kind=="GardenPlant" or kind=="GardenWater" or
   kind=="GardenHarvest" or kind=="GardenSell" then
  return Garden.Process(player,kind,arg,s) and (function()
   context.sync(player)
   if context.onActivity then context.onActivity(player,kind,arg) end
   return true
  end)() or false
 elseif kind=="GoHome" then
  local slot=playerSlots[player]
  if not slot or not playerProperties[player] then
   tell(player,"BUY A HOME AT METRO REALTY BEFORE YOU CAN MOVE IN.")
   return false
  end
  if now-(life.lastHome or -100)<5 then return false end
  local char=player.Character
  if not char then return false end
  life.lastHome=now
  char:PivotTo(CFrame.new(propertyBases[slot]+Vector3.new(0,7,-23)))
  tell(player,"WELCOME HOME • LOT "..slot.." • USE THE SECURITY KEYPAD TO SET VISITOR ACCESS.")
 elseif kind=="SelectCar" then
  if type(arg)~="string" or not Catalog.CarChoices[arg] then
   return false
  end
  if not nearStore(player,"VEHICLE",24) then
   tell(player,"VISIT THE VEHICLE DEALER TO SWITCH YOUR DAILY DRIVER.")
   return false
  end
  if not life.owned[arg] then
   tell(player,"BUY THIS CAR AT THE VEHICLE DEALER FIRST.")
   return false
  end
  life.selectedCar=arg
  tell(player,"GARAGE: "..Catalog.CarChoices[arg].name:upper()..
   " SELECTED. USE THE CAR BUTTON TO SPAWN IT.")
 elseif kind=="Buy" then
  local item=type(arg)=="string" and Catalog.ById[arg]
  if not item or not nearStore(player,item.category,24) then
   tell(player,"VISIT THE CORRECT LIFE CITY STORE TO PURCHASE."); return false
  end
  local seedPacket=Garden.Crops[item.id]~=nil
  if life.owned[item.id] and not seedPacket then
   tell(player,"YOU ALREADY OWN THIS ITEM."); return false
  end
  if s.level<item.level then
   tell(player,"REACH LEVEL "..item.level.." FIRST."); return false
  end
  if s.coins<item.price then
   tell(player,"YOU NEED "..(item.price-s.coins).." MORE COINS."); return false
  end
  s.coins-=item.price
  life.owned[item.id]=true
  if Catalog.CarChoices[item.id] and life.selectedCar=="" then
   life.selectedCar=item.id
  end
  if seedPacket then
   life.garden.seeds[item.id]=math.min(99,(life.garden.seeds[item.id] or 0)+3)
   tell(player,"SEED PACK ADDED: 3 "..item.name.." PLANTINGS.")
  end
  if item.id=="CAMERA" or item.id=="GARDEN_TROWEL" or
   item.id=="WATERING_CAN" then Life.GiveCamera(player) end
  if item.category=="PROPERTY" or item.category=="HOME" or
   item.id=="SMART_TV" or item.id=="GAME_CONSOLE" or
   item.id=="WORKSTATION" or item.id=="DESKTOP_PC" or
   item.id=="LAPTOP" then
   Life.RefreshProperty(player)
  end
  tell(player,"PURCHASED: "..item.name.."! THIS IS AN IN-GAME ITEM.")
 elseif kind=="Publish" then
  if life.career~="CREATOR" or
   not nearbyEither(player,workSites.CREATOR,downtownWorkSites.CREATOR,18) then
   tell(player,"BECOME A CREATOR AND VISIT THE RECORDING STUDIO."); return false
  end
  if not life.owned.PHONE or not life.owned.CAMERA then
   tell(player,"BUY A PHONE AND CAMERA BEFORE RECORDING."); return false
  end
  if now-life.lastPost<24 then
   tell(player,"EDIT YOUR NEXT VIDEO • WAIT FOR THE POST COOLDOWN."); return false
  end
  local char=player.Character
  if not char or not char:FindFirstChild("Creator Camera") then
   tell(player,"EQUIP YOUR CREATOR CAMERA BEFORE RECORDING.")
   return false
  end
  life.lastPost=now; life.uploads+=1
  local production=life.owned.WORKSTATION and 4 or life.owned.MIC and 2 or 1
  local newFollowers=math.min(1500,10+production*12+math.floor(life.followers*.04))
  life.followers=math.min(10000000,life.followers+newFollowers)
  life.reputation=math.min(1000000,life.reputation+production)
  local revenue=math.min(220,8+math.floor(life.followers/100)+production*4)
  context.reward(player,revenue,20+production*4,0)
  tell(player,"VIDEO POSTED! +"..newFollowers.." FOLLOWERS • +"..revenue.." COINS")
 elseif kind=="BusinessCollect" then
  if not nearbyEither(player,stores.BUSINESS,downtownStores.BUSINESS,24) then return false end
  if now-life.lastBusiness<90 then
   tell(player,"YOUR BUSINESSES NEED TIME TO SERVE CUSTOMERS."); return false
  end
  local revenue=0
  for id,amount in pairs(Catalog.BusinessPayouts) do
   if life.owned[id] then revenue+=amount end
  end
  if revenue==0 then tell(player,"BUY A BUSINESS FIRST."); return false end
  life.lastBusiness=now
  context.reward(player,revenue,10,0)
  tell(player,"COLLECTED "..revenue.." COINS FROM YOUR BUSINESSES!")
 elseif kind=="PayFine" then
  if not nearbyEither(player,fineCounter,downtownFineCounter,20) then return false end
  if life.fines<=0 then tell(player,"NO UNPAID FINES."); return false end
  local amount=math.min(s.coins,life.fines)
  s.coins-=amount; life.fines-=amount
  tell(player,"PAID "..amount.." COINS TOWARD COURT FINES.")
 else return false end
 context.sync(player)
 if context.onActivity then context.onActivity(player,kind,arg) end
 return true
end
local function arrest(player,s,officerUnit)
 if Life.IsJailed(player) then return end
 local life=s.life
 local fine=math.min(s.coins,math.max(15,math.floor(s.heat*.6)))
 s.coins-=fine
 life.fines=math.min(1000000,life.fines+math.floor(s.heat*.3))
 life.arrests+=1
 life.jailUntil=os.clock()+20
 s.heat=0
 officerUnit.model:SetAttribute("Behavior","Arrest")
 local char=player.Character
 if char then char:PivotTo(CFrame.new(jailCenter+Vector3.new(0,2,0))) end
 context.sync(player)
 tell(player,"ARRESTED BY POLICE! 20s JAIL • "..fine..
  " COIN FINE • YOUR GEAR IS SAFE.")
end
function Life.Start()
 local elapsed=0
 local needsElapsed=0
 RunService.Heartbeat:Connect(function(dt)
  if not world or not world.Parent then return end
  elapsed+=dt
  needsElapsed+=dt
  if needsElapsed>=120 then
   needsElapsed=0
   for _,player in ipairs(Players:GetPlayers()) do
    local state=profile(player)
    if state and state.life then
     local needs=state.life.needs
     needs.energy=math.max(0,needs.energy-2)
     needs.hunger=math.max(0,needs.hunger-2)
     needs.hygiene=math.max(0,needs.hygiene-1)
     needs.fun=math.max(0,needs.fun-1)
     Life.Sync(player)
    end
   end
  end
  if elapsed<.2 then return end
  local step=math.min(elapsed,.25); elapsed=0
  local now=os.clock()
  for _,player in ipairs(Players:GetPlayers()) do
   local s=profile(player)
   if s and s.life and s.life.jailUntil>0 then
    if now>=s.life.jailUntil then
     s.life.jailUntil=0
     local char=player.Character
     if char then char:PivotTo(CFrame.new(townCenter+Vector3.new(105,7,12))) end
     context.sync(player)
     tell(player,"RELEASED! YOU CAN RETURN TO WORK AND REBUILD REPUTATION.")
    elseif not nearby(player,
      {Position=jailCenter},20) then
     local char=player.Character
     if char then char:PivotTo(CFrame.new(jailCenter+Vector3.new(0,2,0))) end
    end
   end
  end
  for _,unit in ipairs(policeUnits) do
   local closest,dist=nil,85
   for _,player in ipairs(Players:GetPlayers()) do
    local s=profile(player)
    local r=root(player)
    if s and s.life and not Life.IsJailed(player) and
     s.heat>=40 and r and (r.Position-unit.position).Magnitude<dist then
     closest=player; dist=(r.Position-unit.position).Magnitude
    end
   end
   if closest then
    if unit.target~=closest then unit.target=closest; unit.started=now end
    unit.model:SetAttribute("Behavior","Pursuit")
    local r=root(closest)
    if r then
     local delta=Vector3.new(r.Position.X-unit.position.X,0,
      r.Position.Z-unit.position.Z)
     if delta.Magnitude>1 then
      local direction=delta.Unit
      unit.position+=direction*math.min(delta.Magnitude,step*18)
      unit.model:PivotTo(CFrame.lookAt(unit.position,unit.position+direction))
     end
     if delta.Magnitude<8 and now-unit.started>5 then
      local s=profile(closest)
      if s then arrest(closest,s,unit) end
      unit.target=nil
     end
    end
   else
    unit.target=nil
    unit.model:SetAttribute("Behavior","Patrol")
    local goal=unit.route[unit.routeIndex]
    local delta=goal-unit.position
    if delta.Magnitude<2 then
     unit.routeIndex=unit.routeIndex%#unit.route+1
    else
     local direction=delta.Unit
     unit.position+=direction*math.min(delta.Magnitude,step*6)
     unit.model:PivotTo(CFrame.lookAt(unit.position,unit.position+direction))
    end
   end
  end
 end)
 Players.PlayerRemoving:Connect(Life.PlayerRemoving)
end
return Life
