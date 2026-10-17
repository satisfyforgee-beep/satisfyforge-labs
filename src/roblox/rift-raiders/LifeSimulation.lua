-- v0.6 LIFE CITY: in-game-only jobs, shops, creator career and law enforcement.
-- Server validates career, level, currency, ownership, cooldowns and proximity.
local Players=game:GetService("Players")
local RunService=game:GetService("RunService")
local Terrain=workspace.Terrain
local Catalog=require(game:GetService("ReplicatedStorage"):WaitForChild("LifeCatalog"))
local Life={}
local context,world,folder
local stores={}
local workSites={}
local careerSites={}
local taskSites={}
local policeUnits={}
local lastAction={}
local fineCounter=nil
local foodCounter=nil
local restCounter=nil
local publicMealCooldown={}
local propertySlots={}
local playerSlots={}
local playerProperties={}
local propertyBases={
 Vector3.new(-115,0,1712),Vector3.new(-69,0,1712),
 Vector3.new(-23,0,1712),Vector3.new(23,0,1712),
 Vector3.new(69,0,1712),Vector3.new(115,0,1712),
}
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
local function profile(player)
 return context and context.getProfile(player)
end
local function tell(player,msg) context.tell(player,msg) end
function Life.Normalize(value)
 value=type(value)=="table" and value or {}
 return {
  career=Catalog.SanitizeCareer(value.career),
  owned=Catalog.SanitizeOwned(value.owned),
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
  },
  lastWork=0,lastPost=0,lastBusiness=0,jailUntil=0,activeShift=nil,
 }
end
function Life.Serialize(value)
 local s=Life.Normalize(value)
 return {career=s.career,owned=s.owned,followers=s.followers,
  uploads=s.uploads,shifts=s.shifts,reputation=s.reputation,
  fines=s.fines,arrests=s.arrests,needs=s.needs}
end
function Life.Sync(player)
 local s=profile(player)
 if not s or not s.life then return end
 local life=s.life
 player:SetAttribute("RRLifeCareer",life.career)
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
 player:SetAttribute("RRLifeTaskName",nextTarget and
  nextTarget:GetAttribute("TaskLabel") or
  (shift and "RETURN TO YOUR WORKPLACE FOR WAGES" or ""))
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
 }
 for _,entry in ipairs(entries) do
  local category,name,x,z,color=unpack(entry)
  local counter=venue(folder,name,townCenter+Vector3.new(x,0,z),color)
  stores[category]=counter
  prompt(counter,"BROWSE","Shop: "..name,function(player)
   tell(player,"OPEN LIFE SHOP • "..name.." • WALK NEAR THE COUNTER TO BUY")
  end)
 end
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
   local actions=steps[id]
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
function Life.RefreshProperty(player)
 local s=profile(player)
 if not s or not s.life then return end
 local owned=s.life.owned
 local tier=owned.MANSION and "MANSION" or
  owned.TOWNHOUSE and "TOWNHOUSE" or
  owned.APARTMENT and "APARTMENT" or nil
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
 local width=tier=="MANSION" and 36 or tier=="TOWNHOUSE" and 29 or 24
 local floors=tier=="MANSION" and 3 or tier=="TOWNHOUSE" and 2 or 1
 local height=floors*10
 local color=tier=="MANSION" and Color3.fromRGB(216,211,199) or
  tier=="TOWNHOUSE" and Color3.fromRGB(183,143,115) or
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
 for _,floorIndex in ipairs({2,3}) do
  if floorIndex<=floors then
   part(m,"Upper Level Floor",Vector3.new(width-1,.7,25),
    center+Vector3.new(0,3+(floorIndex-1)*10,0),
    Color3.fromRGB(145,105,77),Enum.Material.WoodPlanks,true)
  end
 end
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
 part(m,"Property Entrance",Vector3.new(6,8,.5),
  center+Vector3.new(0,7,-13.5),
  Color3.fromRGB(76,92,108),Enum.Material.WoodPlanks,false)
 textSign(m,tier.." • "..player.DisplayName,
  center+Vector3.new(0,height+12,-15),Color3.fromRGB(255,235,169))
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
end
function Life.GiveCamera(player)
 local s=profile(player)
 if not s or not s.life or not s.life.owned.CAMERA then return end
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
  if not career or not nearby(player,careerSites[arg],17) then return false end
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
   not nearby(player,workSites[arg],18) then return false end
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
   tell(player,"SHIFT STARTED: "..career.name..
    " • COMPLETE THE TWO WORK TASKS MARKED NEARBY.")
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
  tell(player,"SHIFT COMPLETED! +"..career.wage.." COINS • +14 XP")
 elseif kind=="Task" then
  local shift=life.activeShift
  if type(arg)~="string" or not Catalog.CareerById[arg] or
   not shift or shift.id~=arg or life.career~=arg then return false end
  local expected=shift.progress+1
  if type(step)~="number" or step~=expected or step>2 or
   not taskSites[arg] or not nearby(player,taskSites[arg][step],15) then
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
  if arg~="COMMUNITY" or not nearby(player,foodCounter,17) then return false end
  if now-(publicMealCooldown[player] or -1000)<45 then
   tell(player,"THE KITCHEN IS PREPARING MORE MEALS • COME BACK SOON.")
   return false
  end
  publicMealCooldown[player]=now
  life.needs.hunger=math.min(100,life.needs.hunger+50)
  tell(player,"ATE A FREE COMMUNITY MEAL • HUNGER RESTORED!")
 elseif kind=="Rest" then
  if arg~="PUBLIC" or not nearby(player,restCounter,17) then return false end
  life.needs.energy=math.min(100,life.needs.energy+25)
  tell(player,"RESTED AT THE PARK • ENERGY RESTORED!")
 elseif kind=="Buy" then
  local item=type(arg)=="string" and Catalog.ById[arg]
  if not item or not nearby(player,stores[item.category],24) then
   tell(player,"VISIT THE CORRECT LIFE CITY STORE TO PURCHASE."); return false
  end
  if life.owned[item.id] then tell(player,"YOU ALREADY OWN THIS ITEM."); return false end
  if s.level<item.level then
   tell(player,"REACH LEVEL "..item.level.." FIRST."); return false
  end
  if s.coins<item.price then
   tell(player,"YOU NEED "..(item.price-s.coins).." MORE COINS."); return false
  end
  s.coins-=item.price
  life.owned[item.id]=true
  if item.id=="CAMERA" then Life.GiveCamera(player) end
  if item.category=="PROPERTY" then Life.RefreshProperty(player) end
  tell(player,"PURCHASED: "..item.name.."! THIS IS AN IN-GAME ITEM.")
 elseif kind=="Publish" then
  if life.career~="CREATOR" or not nearby(player,workSites.CREATOR,18) then
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
  if not nearby(player,stores.BUSINESS,24) then return false end
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
  if not nearby(player,fineCounter,20) then return false end
  if life.fines<=0 then tell(player,"NO UNPAID FINES."); return false end
  local amount=math.min(s.coins,life.fines)
  s.coins-=amount; life.fines-=amount
  tell(player,"PAID "..amount.." COINS TOWARD COURT FINES.")
 else return false end
 context.sync(player)
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
