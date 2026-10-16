-- SatisfyForge: Tile Panic - playable prototype
-- Place this Script in ServerScriptService of a blank Roblox Studio baseplate.
local Players = game:GetService('Players')
local rng = Random.new()
local folder = Instance.new('Folder', workspace); folder.Name='TilePanicArena'
local function part(name, size, pos, color)
  local p=Instance.new('Part');p.Name=name;p.Size=size;p.Position=pos;p.Anchored=true
  p.Material=Enum.Material.Neon;p.Color=color;p.Parent=folder;return p
end
local lobby=part('Lobby',Vector3.new(38,2,28),Vector3.new(0,5,-55),Color3.fromRGB(60,75,145))
local spawn=Instance.new('SpawnLocation');spawn.Name='LobbySpawn';spawn.Size=Vector3.new(8,1,8);spawn.Position=Vector3.new(0,6.6,-55);spawn.Anchored=true;spawn.Neutral=true;spawn.Parent=folder
local tiles={}
for x=1,8 do for z=1,8 do
 local t=part('Tile',Vector3.new(8,1,8),Vector3.new((x-4.5)*8,5,(z-4.5)*8),Color3.fromHSV((x+z)/17,.8,1))
 table.insert(tiles,t)
end end
local active={};local inRound=false
local function teleport(player,pos)
 local root=player.Character and player.Character:FindFirstChild('HumanoidRootPart')
 if root then root.CFrame=CFrame.new(pos);return true end
 return false
end
local function status(message)
 for _,player in ipairs(Players:GetPlayers()) do
  local gui=player:FindFirstChild('PlayerGui')
  if gui then
   local screen=gui:FindFirstChild('TilePanicHUD')
   if not screen then
    screen=Instance.new('ScreenGui');screen.Name='TilePanicHUD';screen.ResetOnSpawn=false;screen.Parent=gui
    local label=Instance.new('TextLabel');label.Name='Status';label.Size=UDim2.fromScale(.85,.09);label.Position=UDim2.fromScale(.075,.03)
    label.BackgroundColor3=Color3.fromRGB(17,18,31);label.BackgroundTransparency=.12;label.TextColor3=Color3.new(1,1,1)
    label.TextScaled=true;label.Font=Enum.Font.GothamBold;label.Parent=screen
   end
   screen.Status.Text=message
  end
 end
end
local function setup(player)
 local stats=Instance.new('Folder');stats.Name='leaderstats';stats.Parent=player
 local wins=Instance.new('IntValue');wins.Name='Wins';wins.Parent=stats
 local coins=Instance.new('IntValue');coins.Name='Coins';coins.Parent=stats
 player.CharacterAdded:Connect(function(character)
  local humanoid=character:WaitForChild('Humanoid')
  humanoid.Died:Connect(function() active[player]=nil end)
  task.wait(.25)
  if inRound then active[player]=nil;teleport(player,Vector3.new(0,11,-55)) end
 end)
end
Players.PlayerAdded:Connect(setup)
for _,p in ipairs(Players:GetPlayers()) do setup(p) end
Players.PlayerRemoving:Connect(function(p) active[p]=nil end)
local function aliveCount()
 local n=0;for p in pairs(active) do if p.Parent==Players then n+=1 end end;return n
end
-- Never award survival to a player who escaped onto the safe lobby platform.
-- Sample between waves so jumping out and returning before the next wave is not exploitable.
task.spawn(function()
 while true do
  if inRound then
   for player in pairs(active) do
    local character=player.Character
    local root=character and character:FindFirstChild('HumanoidRootPart')
    local humanoid=character and character:FindFirstChildOfClass('Humanoid')
    if not root or not humanoid or humanoid.Health<=0
       or root.Position.Y < -4 or root.Position.Y > 60
       or math.abs(root.Position.X)>34 or math.abs(root.Position.Z)>34 then
     active[player]=nil
     teleport(player,Vector3.new(0,12,-55))
    end
   end
  end
  task.wait(.2)
 end
end)
while true do
 inRound=false;table.clear(active)
 for _,tile in ipairs(tiles) do tile.CanCollide=true;tile.Transparency=0;tile.Color=Color3.fromHSV(rng:NextNumber(),.75,1) end
 for t=10,1,-1 do status('TILE PANIC  |  Next round in '..t);task.wait(1) end
 local contestants=Players:GetPlayers()
 if #contestants>0 then
  inRound=true
  local unusedSpawns=table.clone(tiles)
  for _,p in ipairs(contestants) do
   local humanoid=p.Character and p.Character:FindFirstChildOfClass('Humanoid')
   if humanoid and humanoid.Health>0 then
    local tile
    if #unusedSpawns>0 then
     tile=table.remove(unusedSpawns,rng:NextInteger(1,#unusedSpawns))
    else
     tile=tiles[rng:NextInteger(1,#tiles)]
    end
    if teleport(p,tile.Position+Vector3.new(0,7,0)) then active[p]=true end
   end
  end
  for wave=1,18 do
   if aliveCount()==0 then break end
   status('TILE PANIC  |  Wave '..wave..'/18  |  Survivors: '..aliveCount())
   task.wait(math.max(.7,2.1-wave*.07))
   local available={};for _,tile in ipairs(tiles) do if tile.CanCollide then table.insert(available,tile) end end
   for i=1,math.min(#available,math.max(1,math.floor(wave/2))) do
    local idx=rng:NextInteger(1,#available);local tile=table.remove(available,idx)
    tile.Color=Color3.fromRGB(255,55,70)
    task.delay(.5,function() tile.CanCollide=false;tile.Transparency=.85 end)
   end
   task.wait(.8)
  end
  inRound=false
  local winners=aliveCount()
  for p in pairs(active) do
   if p.Parent==Players and p:FindFirstChild('leaderstats') then
    p.leaderstats.Wins.Value+=1;p.leaderstats.Coins.Value+=50
   end
  end
  status('Round over! '..winners..' survivor(s). Winners earn 50 coins!')
  task.wait(5)
  inRound=false
  for _,p in ipairs(Players:GetPlayers()) do teleport(p,Vector3.new(0,12,-55)) end
 end
end
