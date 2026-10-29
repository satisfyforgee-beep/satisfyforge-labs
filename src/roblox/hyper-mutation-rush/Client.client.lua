local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local player=Players.LocalPlayer
local gui=Instance.new("ScreenGui"); gui.Name="HyperMutationRushHUD"; gui.ResetOnSpawn=false
gui.Parent=player:WaitForChild("PlayerGui")
local function label(name,text,size,pos,color)
 local l=Instance.new("TextLabel"); l.Name=name; l.Size=size; l.Position=pos
 l.BackgroundColor3=Color3.fromRGB(32,38,76); l.BackgroundTransparency=.1
 l.TextColor3=color; l.Font=Enum.Font.GothamBlack; l.TextSize=16; l.Text=text
 l.BorderSizePixel=0; l.Parent=gui
 local corner=Instance.new("UICorner"); corner.CornerRadius=UDim.new(0,12); corner.Parent=l
 return l
end
local title=label("Title","HYPER MUTATION RUSH",UDim2.new(.9,0,0,35),UDim2.new(.05,0,0,10),Color3.fromRGB(255,225,69))
local status=label("Status","STAGE 0/12 | SPEED 18",UDim2.new(.9,0,0,32),UDim2.new(.05,0,0,48),Color3.fromRGB(71,234,255))
local coins=label("Coins","0 COINS | 0 MUTATIONS",UDim2.new(.9,0,0,29),UDim2.new(.05,0,0,84),Color3.fromRGB(119,255,146))
local objective=label("Objective","RUN! COLLECT ORBS + JUMP LASERS!",UDim2.new(.9,0,0,35),UDim2.new(.05,0,0,122),Color3.new(1,1,1))
local upgrade=Instance.new("TextButton"); upgrade.Name="SpeedUpgrade"
upgrade.Size=UDim2.fromOffset(150,54); upgrade.AnchorPoint=Vector2.new(1,1)
upgrade.Position=UDim2.new(.97,0,.91,0); upgrade.Text="BUY +2 SPEED"
upgrade.Font=Enum.Font.GothamBlack; upgrade.TextSize=16
upgrade.TextColor3=Color3.new(1,1,1); upgrade.BackgroundColor3=Color3.fromRGB(255,74,161)
upgrade.Parent=gui
local corner=Instance.new("UICorner"); corner.CornerRadius=UDim.new(0,12); corner.Parent=upgrade
upgrade.Activated:Connect(function()
 ReplicatedStorage:WaitForChild("MutationRushAction"):FireServer("BuySpeed")
end)
-- Teleport menu: big world, short time to the fun. Server validates every destination.
local travel=Instance.new("TextButton"); travel.Name="WorldMapButton"
travel.Size=UDim2.fromOffset(142,48); travel.AnchorPoint=Vector2.new(0,1)
travel.Position=UDim2.new(.03,0,.91,0); travel.Text="WORLD MAP"
travel.Font=Enum.Font.GothamBlack; travel.TextSize=16
travel.TextColor3=Color3.new(1,1,1); travel.BackgroundColor3=Color3.fromRGB(69,194,245)
travel.Parent=gui
local travelCorner=Instance.new("UICorner"); travelCorner.CornerRadius=UDim.new(0,12); travelCorner.Parent=travel
local map=Instance.new("ScrollingFrame"); map.Name="WorldMap"
map.Size=UDim2.new(.9,0,.54,0); map.Position=UDim2.new(.05,0,.23,0)
map.BackgroundColor3=Color3.fromRGB(27,35,69); map.BackgroundTransparency=.05
map.BorderSizePixel=0; map.ScrollBarThickness=6; map.Visible=false; map.Parent=gui
local mapCorner=Instance.new("UICorner"); mapCorner.CornerRadius=UDim.new(0,16); mapCorner.Parent=map
local list=Instance.new("UIListLayout"); list.Padding=UDim.new(0,7); list.Parent=map
local mapPad=Instance.new("UIPadding"); mapPad.PaddingTop=UDim.new(0,10)
mapPad.PaddingLeft=UDim.new(0,10); mapPad.PaddingRight=UDim.new(0,10); mapPad.Parent=map
local locations={
 {"RACE","SPEED RACE + LASERS"},{"CITY","CITY DELIVERY"},{"CAVES","CRYSTAL HUNT"},
 {"SKY","SKY PARKOUR"},{"DOME","SURVIVAL DOME"},
 {"TREASURE","TREASURE ISLAND"},{"FESTIVAL","COLOR CHALLENGE"},
}
for i,entry in ipairs(locations) do
 local b=Instance.new("TextButton"); b.Name="Travel"..entry[1]
 b.Size=UDim2.new(1,-10,0,47); b.Text=entry[2]
 b.Font=Enum.Font.GothamBlack; b.TextSize=15; b.TextColor3=Color3.new(1,1,1)
 b.BackgroundColor3=({Color3.fromRGB(255,82,164),Color3.fromRGB(65,185,235),Color3.fromRGB(157,92,255)})[(i-1)%3+1]
 b.Parent=map
 local round=Instance.new("UICorner"); round.CornerRadius=UDim.new(0,10); round.Parent=b
 b.Activated:Connect(function()
  ReplicatedStorage:WaitForChild("MutationRushAction"):FireServer("Travel",entry[1])
  map.Visible=false
 end)
end
map.CanvasSize=UDim2.fromOffset(0,#locations*54+18)
travel.Activated:Connect(function() map.Visible=not map.Visible end)
local petButton=Instance.new("TextButton"); petButton.Name="FreePet"
petButton.Size=UDim2.fromOffset(142,42); petButton.AnchorPoint=Vector2.new(1,1)
petButton.Position=UDim2.new(.97,0,.79,0); petButton.Text="PET: 120 COINS"
petButton.Font=Enum.Font.GothamBlack; petButton.TextSize=13
petButton.TextColor3=Color3.new(1,1,1); petButton.BackgroundColor3=Color3.fromRGB(150,83,244)
petButton.Parent=gui
local petCorner=Instance.new("UICorner"); petCorner.CornerRadius=UDim.new(0,12); petCorner.Parent=petButton
petButton.Activated:Connect(function()
 ReplicatedStorage:WaitForChild("MutationRushAction"):FireServer("BuyPet")
end)
local raceRecord=label("RaceRecord","BEST RACE: -- | BEAT YOUR TIME!",
 UDim2.new(.9,0,0,29),UDim2.new(.05,0,0,199),Color3.fromRGB(125,255,255))
local mutationAbility=label("MutationAbility","MUTATION: FIND A GATE!",
 UDim2.new(.9,0,0,29),UDim2.new(.05,0,0,235),Color3.fromRGB(255,140,225))
local quest=label("WorldQuest","WORLD QUEST: 0/3 ACTIVITIES = 150 COINS",
 UDim2.new(.9,0,0,29),UDim2.new(.05,0,0,164),Color3.fromRGB(255,225,69))
-- First-session call to action: get the player racing immediately.
local raceNow=Instance.new("TextButton"); raceNow.Name="RaceNow"
raceNow.Size=UDim2.fromOffset(148,48); raceNow.AnchorPoint=Vector2.new(.5,1)
raceNow.Position=UDim2.new(.5,0,.92,0); raceNow.Text="RACE NOW!"
raceNow.Font=Enum.Font.GothamBlack; raceNow.TextSize=17
raceNow.TextColor3=Color3.new(1,1,1); raceNow.BackgroundColor3=Color3.fromRGB(48,202,120)
raceNow.Parent=gui
local raceCorner=Instance.new("UICorner"); raceCorner.CornerRadius=UDim.new(0,12); raceCorner.Parent=raceNow
raceNow.Activated:Connect(function()
 ReplicatedStorage:WaitForChild("MutationRushAction"):FireServer("Travel","RACE")
end)
local toast=label("Toast","",UDim2.new(.85,0,0,50),UDim2.new(.075,0,.7,0),Color3.fromRGB(255,223,66))
toast.Visible=false
local seq=0
ReplicatedStorage:WaitForChild("MutationRushEvent").OnClientEvent:Connect(function(message)
 seq+=1; local current=seq
 toast.Text=message; toast.Visible=true
 task.delay(2,function() if seq==current then toast.Visible=false end end)
end)
local function update()
 local stage=player:GetAttribute("MRStage") or 0
 status.Text="STAGE "..stage.."/12 | SPEED "..(player:GetAttribute("MRSpeed") or 18)
 coins.Text=(player:GetAttribute("MRCoins") or 0).." COINS | "..(player:GetAttribute("MRMutations") or 0).." MUTATIONS"
 local best=player:GetAttribute("MRBestTime") or 0
 local active=player:GetAttribute("MRAbility") or ""
 mutationAbility.Text=active~="" and ("ACTIVE MUTATION: "..active.." (18s BOOST)") or "MUTATION: FIND A GATE!"
 raceRecord.Text=best>0 and ("BEST RACE: "..best.."s | BEAT YOUR TIME!") or "BEST RACE: -- | FINISH TO SET A RECORD!"
 quest.Text="WORLD QUEST: "..(player:GetAttribute("MRQuest") or 0).."/3 ACTIVITIES = 150 COINS"
 objective.Text=stage>=12 and "REACH THE GREEN FINISH!" or
  "COLLECT ORBS + DODGE LASERS | NEXT "..(stage+1).."/12"
end
for _,key in ipairs({"MRStage","MRSpeed","MRCoins","MRMutations","MRQuest","MRBestTime","MRAbility"}) do
 player:GetAttributeChangedSignal(key):Connect(update)
end
update()
print("SF_MUTATION_CLIENT_READY")
