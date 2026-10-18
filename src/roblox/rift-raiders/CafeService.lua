-- v0.18: Real barista mini-game in the imported Modern Downtown.
-- Customers order one of three drinks. Brew the matching recipe and deliver
-- it after preparation; all interactions are server-verified in the world.
local Cafe={}
Cafe.Recipes={"ESPRESSO","LATTE","MOCHA"}
local state={}
local stations={}
local handlers
local function near(player,node,radius)
 local character=player.Character
 local root=character and character:FindFirstChild("HumanoidRootPart")
 return root and node and node.Parent and
  (root.Position-node.Position).Magnitude<=(radius or 14)
end
local function create(parent,name,size,cf,color,material)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf;p.Color=color
 p.Material=material or Enum.Material.WoodPlanks
 p.Anchored=true;p.CanCollide=false;p.CanTouch=false
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=parent
 return p
end
local function billboard(node,title,subtitle)
 local ui=Instance.new("BillboardGui")
 ui.Name="Cafe Menu Sign";ui.Size=UDim2.fromOffset(225,70)
 ui.StudsOffsetWorldSpace=Vector3.new(0,3.4,0)
 ui.MaxDistance=90;ui.Parent=node
 local text=Instance.new("TextLabel")
 text.Size=UDim2.fromScale(1,1);text.BackgroundTransparency=.15
 text.BackgroundColor3=Color3.fromRGB(54,40,36)
 text.TextColor3=Color3.fromRGB(255,240,213)
 text.Font=Enum.Font.GothamBold;text.TextSize=17;text.TextWrapped=true
 text.Text=title.."\n"..subtitle;text.Parent=ui
end
local function prompt(part,action,name,callback)
 local p=Instance.new("ProximityPrompt")
 p.ActionText=action;p.ObjectText=name;p.MaxActivationDistance=12
 p.RequiresLineOfSight=false;p.HoldDuration=.55;p.Parent=part
 p.Triggered:Connect(callback)
 return p
end
local function coffeeCup(model,cf,color)
 local cup=create(model,"Porcelain Coffee Cup",
  Vector3.new(.85,.8,.85),cf,color,Enum.Material.SmoothPlastic)
 cup.Shape=Enum.PartType.Cylinder
 create(model,"Coffee Surface",Vector3.new(.65,.05,.65),
  cf*CFrame.new(0,.43,0),Color3.fromRGB(76,39,26),
  Enum.Material.SmoothPlastic).Shape=Enum.PartType.Cylinder
 return cup
end
function Cafe.Build(world,options)
 handlers=options
 local folder=Instance.new("Folder")
 folder.Name="Downtown Interactive Coffee Bar";folder.Parent=world
 local origin=CFrame.new(-36,4,2281)
 local foundation=create(folder,"Cafe Porcelain Tile",
  Vector3.new(24,.5,14),origin*CFrame.new(0,-.7,0),
  Color3.fromRGB(192,186,168),Enum.Material.Concrete)
 foundation.CanCollide=true
 local counter=create(folder,"Solid Oak Service Counter",
  Vector3.new(22,3.2,3),origin*CFrame.new(0,1.2,3),
  Color3.fromRGB(136,97,72),Enum.Material.WoodPlanks)
 counter.CanCollide=true
 create(folder,"Cafe Marble Worktop",
  Vector3.new(22,.25,3.7),origin*CFrame.new(0,2.8,3),
  Color3.fromRGB(215,212,193),Enum.Material.Marble)
 local awning=create(folder,"Cafe Canvas Awning",
  Vector3.new(25,.5,6),origin*CFrame.new(0,8,1.4),
  Color3.fromRGB(140,102,74),Enum.Material.Fabric)
 for _,x in ipairs({-10.5,10.5}) do
  create(folder,"Cafe Copper Awning Post",
   Vector3.new(.35,9,.35),origin*CFrame.new(x,4.1,1.2),
   Color3.fromRGB(139,110,73),Enum.Material.Metal)
 end
 local signs=create(folder,"Cafe Menu Board",Vector3.new(12,4,.4),
  origin*CFrame.new(0,6.15,5.2),
  Color3.fromRGB(45,49,50),Enum.Material.Slate)
 billboard(signs,"THE BEAN & BREW","ESPRESSO • LATTE • MOCHA")
 for i,recipe in ipairs(Cafe.Recipes) do
  local x=-7.5+(i-1)*7.5
  local brew=create(folder,"Coffee Brew "..recipe,
   Vector3.new(4,3.6,2.6),
   origin*CFrame.new(x,4.5,3.4),
   Color3.fromRGB(62,70,72),Enum.Material.Metal)
  create(folder,recipe.." Espresso Drip Head",
   Vector3.new(1.4,1.1,.8),
   brew.CFrame*CFrame.new(0,.15,-1.4),
   Color3.fromRGB(204,205,194),Enum.Material.Metal)
  local lamp=create(folder,recipe.." Espresso Machine Lamp",
   Vector3.new(.55,.55,.25),
   brew.CFrame*CFrame.new(0,1,-1.46),
   recipe=="MOCHA" and Color3.fromRGB(141,83,62) or
    recipe=="LATTE" and Color3.fromRGB(188,150,84) or
    Color3.fromRGB(94,178,150),Enum.Material.Neon)
  prompt(brew,"BREW "..recipe,recipe.." ESPRESSO MACHINE",function(player)
   if handlers and handlers.process then
    handlers.process(player,"CafeBrew",recipe)
   end
  end)
  stations[recipe]=brew
  coffeeCup(folder,origin*CFrame.new(x,3.5,1),
   Color3.fromRGB(245,244,227))
 end
 for i=-3,3 do
  create(folder,"Cafe Menu Pastry Shelf",Vector3.new(1.3,.8,.9),
   origin*CFrame.new(i*2,3.2,-2.6),
   Color3.fromRGB(178,126,75),Enum.Material.WoodPlanks)
  local bun=create(folder,"Fresh Bakery Croissant",
   Vector3.new(1.15,.55,.8),
   origin*CFrame.new(i*2,3.6,-2.6),
   Color3.fromRGB(219,167,76),Enum.Material.SmoothPlastic)
  bun.Shape=Enum.PartType.Ball
 end
 local serve=create(folder,"Cafe Customer Service Register",
  Vector3.new(4,3,2),origin*CFrame.new(0,1.6,-3.8),
  Color3.fromRGB(97,116,110),Enum.Material.Metal)
 serve.CanCollide=true
 billboard(serve,"SERVE CUSTOMER","COMPLETE CORRECT ORDER")
 prompt(serve,"SERVE READY DRINK","CUSTOMER PICKUP",function(player)
  if handlers and handlers.process then
   handlers.process(player,"CafeServe")
  end
 end)
 stations.SERVE=serve
 folder:SetAttribute("Recipes",3)
 folder:SetAttribute("InteractiveOrders",true)
 folder:SetAttribute("NoExternalScripts",true)
 state.folder=folder
 return folder
end
function Cafe.Assign(shift)
 if type(shift)~="table" then return nil end
 local recipe=Cafe.Recipes[math.random(1,#Cafe.Recipes)]
 shift.cafeOrder=recipe
 shift.cafeBrewed=false
 return recipe
end
function Cafe.Process(player,kind,arg,shift)
 if not handlers or not shift or shift.id~="BARISTA" or
  type(shift.cafeOrder)~="string" then return false end
 local now=os.clock()
 if kind=="CafeBrew" then
  if type(arg)~="string" or not stations[arg] or
   not near(player,stations[arg],6.5) then return false end
  if shift.progress~=0 or now-shift.started<1.5 then
   handlers.tell(player,"START YOUR SHIFT AND GIVE THE COFFEE TIME TO BREW.")
   return false
  end
  if arg~=shift.cafeOrder then
   handlers.tell(player,"WRONG DRINK! CUSTOMER ORDERED "..shift.cafeOrder..
    ". SELECT THE MATCHING MACHINE.")
   return false
  end
  shift.progress=1;shift.taskAt=now;shift.cafeBrewed=true
  handlers.tell(player,"PERFECT "..arg.."! TAKE THE DRINK TO THE CUSTOMER REGISTER.")
 elseif kind=="CafeServe" then
  if not near(player,stations.SERVE,10) or
   shift.progress~=1 or not shift.cafeBrewed then return false end
  if now-shift.taskAt<1.5 then
   handlers.tell(player,"FINISH STEAMING THE DRINK BEFORE SERVING.")
   return false
  end
  shift.progress=2;shift.taskAt=now
  handlers.reward(player,12,5,0)
  handlers.tell(player,"CUSTOMER LOVED IT! +12 COIN TIP • RETURN TO SHIFT COUNTER.")
 else return false end
 handlers.sync(player)
 return true
end
return Cafe
