-- v0.22: Server-verified checkout-and-restock role at the downtown corner market.
-- No client-selected orders, extra background loops or paid marketplace assets.
local Characters=require(script.Parent:WaitForChild("VenueCharacters"))
local Retail={}
Retail.Products={"GROCERIES","ELECTRONICS","TOYS"}
local checkout={}
local shelves={}
local attendants={}
local handlers
local function part(parent,name,size,cf,color,material,collides)
 local p=Instance.new("Part")
 p.Name=name;p.Size=size;p.CFrame=cf;p.Color=color
 p.Material=material or Enum.Material.SmoothPlastic
 p.Anchored=true;p.CanCollide=collides==true;p.CanTouch=false
 p.TopSurface=Enum.SurfaceType.Smooth
 p.BottomSurface=Enum.SurfaceType.Smooth;p.Parent=parent
 return p
end
local function textSign(base,title,subtitle)
 local gui=Instance.new("BillboardGui")
 gui.Name="Market Wayfinding";gui.Size=UDim2.fromOffset(210,63)
 gui.MaxDistance=75;gui.StudsOffsetWorldSpace=Vector3.new(0,3.1,0)
 gui.Parent=base
 local label=Instance.new("TextLabel")
 label.Size=UDim2.fromScale(1,1);label.TextWrapped=true
 label.BackgroundColor3=Color3.fromRGB(31,45,59)
 label.BackgroundTransparency=.08
 label.TextColor3=Color3.fromRGB(246,236,202)
 label.TextSize=14;label.Font=Enum.Font.GothamBold
 label.Text=title.."\n"..subtitle;label.Parent=gui
end
local function interaction(node,verb,product,kind)
 local prompt=Instance.new("ProximityPrompt")
 prompt.ActionText=verb;prompt.ObjectText=product
 prompt.MaxActivationDistance=9;prompt.HoldDuration=.5
 prompt.RequiresLineOfSight=false;prompt.Parent=node
 prompt.Triggered:Connect(function(player)
  if handlers and handlers.process then
   handlers.process(player,kind,product)
  end
 end)
end
local function near(player,node,dist)
 local root=player.Character and player.Character:FindFirstChild("HumanoidRootPart")
 return root and node and node.Parent and
  (root.Position-node.Position).Magnitude<=(dist or 9)
end
function Retail.Build(world,options)
 handlers=options
 table.clear(checkout);table.clear(shelves);table.clear(attendants)
 local folder=Instance.new("Folder")
 folder.Name="Downtown Hands-On Corner Market";folder.Parent=world
 local base=CFrame.new(-72,3,2287)
 part(folder,"Market Terrazzo Floor",Vector3.new(35,.65,31),
  base*CFrame.new(0,-.55,0),Color3.fromRGB(185,174,157),
  Enum.Material.Concrete,true)
 local fascia=part(folder,"Corner Market Fascia",Vector3.new(31,4,1),
  base*CFrame.new(0,8.5,14),
  Color3.fromRGB(54,83,95),Enum.Material.Metal,false)
 textSign(fascia,"THE CORNER MARKET","SCAN • RESTOCK • EARN")
 for i,product in ipairs(Retail.Products) do
  local x=(i-2)*10
  local hue={
   GROCERIES=Color3.fromRGB(130,162,98),
   ELECTRONICS=Color3.fromRGB(85,153,177),
   TOYS=Color3.fromRGB(189,120,125),
  }
  local checkoutDesk=part(folder,"Retail Checkout "..product,
   Vector3.new(7.5,2.6,3),base*CFrame.new(x,1.2,-7),
   Color3.fromRGB(105,83,69),Enum.Material.Wood,true)
  part(folder,product.." Barcode Scanner",Vector3.new(1.7,.55,1.15),
   checkoutDesk.CFrame*CFrame.new(-1,1.55,-.1),
   Color3.fromRGB(45,59,65),Enum.Material.Metal,false)
  part(folder,product.." Scannable Carton",Vector3.new(2.1,1.2,1.7),
   checkoutDesk.CFrame*CFrame.new(1.2,1.8,0),
   hue[product],Enum.Material.SmoothPlastic,false)
  textSign(checkoutDesk,product.." CHECKOUT","SCAN MATCHING CUSTOMER ITEM")
  interaction(checkoutDesk,"SCAN "..product,product,"RetailScan")
  checkout[product]=checkoutDesk
  local shelf=part(folder,"Retail Restock "..product,
   Vector3.new(7,5,2.6),base*CFrame.new(x,2.65,8),
   Color3.fromRGB(86,94,97),Enum.Material.Metal,true)
  for row=1,2 do
   part(folder,product.." Shelf Row "..row,Vector3.new(6.6,.18,3),
    shelf.CFrame*CFrame.new(0,-2.4+row*1.5,0),
    Color3.fromRGB(190,190,180),Enum.Material.Metal,false)
   for box=1,3 do
    part(folder,product.." Stock "..row.."-"..box,
     Vector3.new(1.25,.9,.9),
     shelf.CFrame*CFrame.new((box-2)*1.7,-2.1+row*1.5,-.3),
     hue[product],Enum.Material.SmoothPlastic,false)
   end
  end
  textSign(shelf,product.." SHELF","RESTOCK ASSIGNED GOODS")
  interaction(shelf,"RESTOCK "..product,product,"RetailStock")
  shelves[product]=shelf
 end
 attendants[1]=Characters.Create(folder,"Corner Market Cashier A",
  base*CFrame.new(-15,0,-11),"MORGAN • CASHIER",
  Color3.fromRGB(78,124,104),function(player)
   if handlers and handlers.process then handlers.process(player,"RetailGuide") end
  end)
 attendants[2]=Characters.Create(folder,"Corner Market Cashier B",
  base*CFrame.new(15,0,-11),"ALEX • CUSTOMER CARE",
  Color3.fromRGB(68,106,142),function(player)
   if handlers and handlers.process then handlers.process(player,"RetailGuide") end
  end)
 folder:SetAttribute("RetailNPCCount",#attendants)
 folder:SetAttribute("RetailSkuCount",#Retail.Products)
 folder:SetAttribute("ServerValidatedOrder",true)
 folder:SetAttribute("NoBackgroundLoops",true)
 return folder
end
function Retail.Assign(shift)
 if type(shift)~="table" then return nil end
 local scan=Retail.Products[math.random(1,#Retail.Products)]
 local stock=Retail.Products[math.random(1,#Retail.Products)]
 shift.retailScanSku=scan;shift.retailStockSku=stock
 shift.retailScanned=false
 return scan,stock
end
function Retail.Process(player,kind,product,shift)
 if kind=="RetailGuide" then
  local closeToStaff=false
  for _,staff in ipairs(attendants) do
   local root=staff and staff.PrimaryPart
   if root and near(player,root,8) then closeToStaff=true;break end
  end
  if not closeToStaff or not handlers then return false end
  if shift and shift.id=="RETAIL" and shift.retailScanSku then
   local message=shift.progress==0 and ("YOUR CUSTOMER NEEDS "..shift.retailScanSku..
    ". SCAN IT AT THE MATCHING CHECKOUT.") or
    shift.progress==1 and ("THANKS! RESTOCK "..shift.retailStockSku..
    " ON ITS MATCHING SHELF.") or
    "GREAT WORK! RETURN TO RETAIL FOR WAGES."
   handlers.tell(player,message)
  else handlers.tell(player,"APPLY FOR RETAIL AT CITY JOBS, START YOUR SHIFT, THEN SCAN AND RESTOCK MATCHING GOODS.") end
  return true
 end
 if not handlers or not shift or shift.id~="RETAIL" or
  type(shift.retailScanSku)~="string" then return false end
 local now=os.clock()
 if kind=="RetailScan" then
  if type(product)~="string" or not checkout[product] or
   not near(player,checkout[product],9) or shift.progress~=0 or
   now-shift.started<1.5 then return false end
  if product~=shift.retailScanSku then
   handlers.tell(player,"WRONG CUSTOMER ITEM. THE ORDER IS "..shift.retailScanSku..".")
   return false
  end
  shift.progress=1;shift.taskAt=now;shift.retailScanned=true
  handlers.tell(player,"ITEM SCANNED! RESTOCK "..shift.retailStockSku..
   " ON THE LABELED DISPLAY SHELF.")
 elseif kind=="RetailStock" then
  if type(product)~="string" or not shelves[product] or
   not near(player,shelves[product],9) or shift.progress~=1 or
   not shift.retailScanned then return false end
  if now-shift.taskAt<1.5 then
   handlers.tell(player,"FINISH PREPARING THE RESTOCK CART FIRST.")
   return false
  end
  if product~=shift.retailStockSku then
   handlers.tell(player,"WRONG SHELF! THE ORDER NEEDS "..shift.retailStockSku..".")
   return false
  end
  shift.progress=2;shift.taskAt=now
  handlers.reward(player,8,4,0)
  handlers.tell(player,"SHELF RESTOCKED • +8 COIN CUSTOMER TIP! RETURN TO THE RETAIL WORKPLACE FOR WAGES.")
 else return false end
 handlers.sync(player)
 return true
end
return Retail
