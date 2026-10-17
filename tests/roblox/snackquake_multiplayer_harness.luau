-- Snackquake two-client server authority regression.
local StudioTestService = game:GetService("StudioTestService")
local ServerScriptService = game:GetService("ServerScriptService")
local StarterPlayer = game:GetService("StarterPlayer")
print("SF_SNACK_MP_BEGIN")
local serverTest = Instance.new("Script")
serverTest.Name = "SFSnackquakeMultiplayerServerTest"
serverTest.Source = [==[
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local StudioTestService = game:GetService("StudioTestService")
local Data = require(game:GetService("ServerScriptService"):WaitForChild("SnackquakeServer"):WaitForChild("PlayerData"))
local function waitFor(fn, seconds)
 local deadline = os.clock() + seconds
 while os.clock() < deadline do
  local ok, value = pcall(fn)
  if ok and value then return value end
  task.wait(.1)
 end
 return nil
end
local function fail(reason)
 warn("SF_SNACK_MP_FAIL " .. reason)
 StudioTestService:EndTest("FAIL:" .. reason)
end
local channel=Instance.new("RemoteEvent")
channel.Name="SFSnackquakeMultiplayerProbe"
channel.Parent=ReplicatedStorage
local players = waitFor(function()
 local list = Players:GetPlayers()
 if #list >= 2 and list[1]:GetAttribute("SFReady") and list[2]:GetAttribute("SFReady") then return list end
end, 35)
if not players then
 local list=Players:GetPlayers()
 warn("SF_SNACK_MP_DIAG players="..#list)
 for _,p in ipairs(list) do warn("SF_SNACK_MP_DIAG "..p.Name.." ready="..tostring(p:GetAttribute("SFReady")).." data="..tostring(Data.get(p)~=nil)) end
 fail("players_not_ready") return
end
local p1,p2=players[1],players[2]
local rec1,rec2=Data.get(p1),Data.get(p2)
if not rec1 or not rec2 or rec1 == rec2 or rec1.profile == rec2.profile then
 fail("profiles_not_independent") return
end
if rec1.canSave or rec2.canSave then fail("studio_would_write_live_data") return end
local shared=ReplicatedStorage:WaitForChild("SnackquakeShared", 10)
local action=shared and shared:WaitForChild("Action", 10)
if not action then fail("missing_action_remote") return end
local responses={}
channel.OnServerEvent:Connect(function(player,token,ok)
 responses[player]=responses[player] or {}
 responses[player][token]=ok
end)
local function ask(player,token,name,payload)
 channel:FireClient(player,token,name,payload)
 return waitFor(function() return responses[player] and responses[player][token] end, 7)
end
rec1.profile.fizz=100; rec2.profile.fizz=100
rec1.profile.speed=0; rec2.profile.speed=0
if not ask(p1,"upgrade_one","upgrade") then fail("first_client_not_responding") return end
if not waitFor(function() return rec1.profile.speed==1 end, 4) then fail("upgrade_did_not_apply") return end
if rec1.profile.fizz~=50 or rec2.profile.fizz~=100 or rec2.profile.speed~=0 then
 fail("upgrade_cross_player_mutation") return
end
print("SF_SNACK_MP_CHECK upgrade_isolated PASS")
task.wait(.25)
if not ask(p2,"upgrade_two","upgrade") then fail("second_client_not_responding") return end
if not waitFor(function() return rec2.profile.speed==1 end, 4) then fail("second_upgrade_did_not_apply") return end
if rec2.profile.fizz~=50 or rec1.profile.fizz~=50 or rec1.profile.speed~=1 then
 fail("second_upgrade_cross_player") return
end
print("SF_SNACK_MP_CHECK second_client_isolated PASS")
task.wait(.25)
if not ask(p1,"unowned_equip","equip","cosmocroissant") then fail("equip_client_not_responding") return end
task.wait(.25)
if rec1.profile.equipped~="" or rec2.profile.equipped~="" then
 fail("unowned_creature_equipped") return
end
print("SF_SNACK_MP_CHECK unowned_equip_rejected PASS")
task.wait(.25)
if not ask(p1,"unowned_fuse","fuse","cosmocroissant") then fail("fuse_client_not_responding") return end
task.wait(.25)
if (rec1.profile.evolution.cosmocroissant or 0)~=0 or (rec2.profile.evolution.cosmocroissant or 0)~=0 then
 fail("unowned_fuse_succeeded") return
end
print("SF_SNACK_MP_CHECK unowned_fuse_rejected PASS")
rec1.profile.fizz=49; rec1.profile.speed=0
task.wait(.25)
if not ask(p1,"insufficient_funds","upgrade") then fail("funds_client_not_responding") return end
task.wait(.25)
if rec1.profile.fizz~=49 or rec1.profile.speed~=0 or rec2.profile.fizz~=50 then
 fail("insufficient_funds_bypass") return
end
print("SF_SNACK_MP_CHECK insufficient_funds_rejected PASS")
print("SF_SNACK_MP_SERVER_PASS players=2")
StudioTestService:EndTest("PASS:snackquake_multiplayer")
]==]
serverTest.Parent=ServerScriptService
local clientTest=Instance.new("LocalScript")
clientTest.Name="SFSnackquakeMultiplayerClientTest"
clientTest.Source=[==[
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local channel=ReplicatedStorage:WaitForChild("SFSnackquakeMultiplayerProbe", 20)
local shared=ReplicatedStorage:WaitForChild("SnackquakeShared", 20)
local action=shared:WaitForChild("Action", 20)
channel.OnClientEvent:Connect(function(token,name,payload)
 action:FireServer(name,payload)
 task.wait(.15)
 channel:FireServer(token,true)
end)
]==]
clientTest.Parent=StarterPlayer:WaitForChild("StarterPlayerScripts")
local ok,result=pcall(function()
 return StudioTestService:ExecuteMultiplayerTestAsync(2,"snackquake-action-isolation")
end)
print("SF_SNACK_MP_RESULT ok="..tostring(ok).." result="..tostring(result))
if not ok or result~="PASS:snackquake_multiplayer" then
 error("Snackquake multiplayer regression failed: "..tostring(result))
end
print("SF_SNACK_MP_PASS")
