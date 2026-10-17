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
 objective.Text=stage>=12 and "REACH THE GREEN FINISH!" or
  "COLLECT ORBS + DODGE LASERS | NEXT "..(stage+1).."/12"
end
for _,key in ipairs({"MRStage","MRSpeed","MRCoins","MRMutations"}) do
 player:GetAttributeChangedSignal(key):Connect(update)
end
update()
print("SF_MUTATION_CLIENT_READY")
