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
local policeUnits={}
local lastAction={}
local fineCounter=nil
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
  lastWork=0,lastPost=0,lastBusiness=0,jailUntil=0,activeShift=nil,
 }
end
function Life.Serialize(value)
 local s=Life.Normalize(value)
 return {career=s.career,owned=s.owned,followers=s.followers,
  uploads=s.uploads,shifts=s.shifts,reputation=s.reputation,
  fines=s.fines,arrests=s.arrests}
end
function Life.Sync(player)
 local s=profile(player)
 if not s or not s.life then return end
 local life=s.life
 player:SetAttribute("RRLifeCareer",life.career)
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
 table.insert(policeUnits,{model=m,home=start,position=start,target=nil,started=0})
end
function Life.Build(targetWorld,options)
 context=options; world=targetWorld
 folder=Instance.new("Folder"); folder.Name="Life City Simulation"; folder.Parent=world
 Terrain:FillBlock(CFrame.new(townCenter+Vector3.new(0,-4,0)),
  Vector3.new(330,12,270),Enum.Material.Grass)
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
  local board=part(folder,"Career Board "..career.id,Vector3.new(5,6,1),
   careerCounter.Position+Vector3.new(-12+(i-1)*4,4,-7),
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
 part(m,"Property Main Structure",Vector3.new(width,height,26),
  center+Vector3.new(0,3+height*.5,0),color,Enum.Material.Brick,true)
 part(m,"Property Roof",Vector3.new(width+3,2,30),
  center+Vector3.new(0,4+height,0),
  Color3.fromRGB(48,58,73),Enum.Material.Slate,true)
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
function Life.Process(player,kind,arg)
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
  tell(player,"HIRED: "..career.name.."! FIND YOUR WORKPLACE.")
 elseif kind=="Work" then
  local career=type(arg)=="string" and Catalog.CareerById[arg]
  if not career or arg=="CREATOR" or life.career~=arg or
   not nearby(player,workSites[arg],18) then return false end
  if now-life.lastWork<12 then
   tell(player,"SHIFT REST BREAK • TRY AGAIN SHORTLY."); return false
  end
  if arg=="POLICE" and s.heat>0 then
   tell(player,"POLICE OFFICERS MUST HAVE A CLEAR RECORD."); return false
  end
  if not life.activeShift or life.activeShift.id~=arg then
   life.activeShift={id=arg,started=now}
   tell(player,"SHIFT STARTED: "..career.name..
    " • FINISH YOUR TASK AND RETURN TO THE WORK STATION IN 3 SECONDS.")
   return true
  end
  if now-life.activeShift.started<3 then
   tell(player,"STILL WORKING! COMPLETE THE TASK BEFORE COLLECTING WAGES.")
   return false
  end
  life.activeShift=nil
  life.lastWork=now; life.shifts+=1
  life.reputation=math.min(1000000,life.reputation+1)
  context.reward(player,career.wage,14,0)
  tell(player,"SHIFT COMPLETED! +"..career.wage.." COINS • +14 XP")
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
 RunService.Heartbeat:Connect(function(dt)
  if not world or not world.Parent then return end
  elapsed+=dt
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
    local delta=unit.home-unit.position
    if delta.Magnitude>1 then
     unit.position+=delta.Unit*math.min(delta.Magnitude,step*10)
     unit.model:PivotTo(CFrame.lookAt(unit.position,unit.home))
    end
   end
  end
 end)
 Players.PlayerRemoving:Connect(Life.PlayerRemoving)
end
return Life
