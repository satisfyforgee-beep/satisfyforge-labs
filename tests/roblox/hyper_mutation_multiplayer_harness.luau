local StudioTestService=game:GetService("StudioTestService")
local ServerScriptService=game:GetService("ServerScriptService")
local StarterPlayer=game:GetService("StarterPlayer")
print("SF_MUTATION_MP_BEGIN")
local server=Instance.new("Script")
server.Name="SFMutationMultiplayerServerTest"
server.Source=[==[
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local StudioTestService=game:GetService("StudioTestService")
local function waitFor(fn,secs)
 local endAt=os.clock()+secs
 while os.clock()<endAt do
  local ok,result=pcall(fn)
  if ok and result then return result end
  task.wait(.1)
 end
 return nil
end
local function fail(msg)
 warn("SF_MUTATION_MP_FAIL "..msg)
 StudioTestService:EndTest("FAIL:"..msg)
end
local channel=Instance.new("RemoteEvent")
channel.Name="SFMutationMPProbe"; channel.Parent=ReplicatedStorage
local players=waitFor(function()
 local ps=Players:GetPlayers()
 if #ps>=2 and ps[1]:GetAttribute("MRSpeed") and ps[2]:GetAttribute("MRSpeed") then return ps end
end,45)
if not players then fail("players_not_ready_count="..#Players:GetPlayers()) return end
local a,b=players[1],players[2]
local remote=ReplicatedStorage:WaitForChild("MutationRushAction",10)
if not remote then fail("missing_remote") return end
local responses={}
channel.OnServerEvent:Connect(function(p,id)
 responses[p]=responses[p] or {}
 responses[p][id]=true
end)
local function request(p,id,action,param)
 channel:FireClient(p,id,action,param)
 return waitFor(function() return responses[p] and responses[p][id] end,6)
end
if not request(a,"travel_city","Travel","CITY") then fail("client_a_no_response") return end
local root=waitFor(function() return a.Character and a.Character:FindFirstChild("HumanoidRootPart") end,5)
if not root then fail("a_root_missing") return end
if not waitFor(function() return (root.Position-Vector3.new(170,5,55)).Magnitude<12 end,5) then
 fail("travel_not_applied") return
end
local rootB=waitFor(function() return b.Character and b.Character:FindFirstChild("HumanoidRootPart") end,5)
if not rootB then fail("b_root_missing") return end
if (rootB.Position-Vector3.new(170,5,55)).Magnitude<20 then fail("travel_changed_other_player") return end
print("SF_MUTATION_MP_CHECK travel_isolated PASS")
task.wait(1.7)
if not request(a,"invalid_travel","Travel","NOT_A_ZONE") then fail("invalid_client_no_response") return end
task.wait(.4)
if (root.Position-Vector3.new(170,5,55)).Magnitude>30 then fail("invalid_travel_moved_player") return end
print("SF_MUTATION_MP_CHECK invalid_destination_rejected PASS")
local startCoins=a:GetAttribute("MRCoins") or 0
if not request(a,"buy_without_coins","BuySpeed",nil) then fail("buy_client_no_response") return end
task.wait(.3)
if (a:GetAttribute("MRCoins") or 0)~=startCoins or a:GetAttribute("MRSpeed")~=18 then
 fail("free_upgrade") return
end
print("SF_MUTATION_MP_CHECK insufficient_funds_rejected PASS")
if b:GetAttribute("MRSpeed")~=18 or b:GetAttribute("MRCoins")~=0 then fail("cross_player_state") return end
local function collect(name)
 local item=workspace:WaitForChild("HyperMutationRushWorld"):FindFirstChild(name)
 if not item then fail("missing_"..name) return false end
 a.Character:PivotTo(CFrame.new(item.Position+Vector3.new(0,2,0)))
 task.wait(.7)
 return true
end
if not collect("Cave Crystal 1") then return end
if not waitFor(function() return (a:GetAttribute("MRCoins") or 0)>=10 end,3) then fail("crystal_not_collected") return end
if b:GetAttribute("MRCoins")~=0 then fail("crystal_shared_wallet") return end
print("SF_MUTATION_MP_CHECK cave_crystal_isolated PASS")
if not collect("Treasure Chest") then return end
if not waitFor(function() return (a:GetAttribute("MRCoins") or 0)>=60 end,3) then fail("chest_not_collected") return end
print("SF_MUTATION_MP_CHECK chest_reward PASS")
for i=1,3 do if not collect("Festival Button "..i) then return end end
if not waitFor(function() return (a:GetAttribute("MRCoins") or 0)>=270 end,3) then
 fail("festival_quest_not_awarded_coins="..tostring(a:GetAttribute("MRCoins"))) return
end
if a:GetAttribute("MRQuest")~=0 or b:GetAttribute("MRCoins")~=0 then fail("quest_or_isolation") return end
print("SF_MUTATION_MP_CHECK festival_and_quest PASS")
print("SF_MUTATION_MP_SERVER_PASS players=2")
StudioTestService:EndTest("PASS:mutation_multiplayer")
]==]
server.Parent=ServerScriptService
local client=Instance.new("LocalScript")
client.Name="SFMutationMultiplayerClientTest"
client.Source=[==[
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local channel=ReplicatedStorage:WaitForChild("SFMutationMPProbe",20)
local action=ReplicatedStorage:WaitForChild("MutationRushAction",20)
channel.OnClientEvent:Connect(function(id,kind,arg)
 action:FireServer(kind,arg)
 task.wait(.15)
 channel:FireServer(id)
end)
]==]
client.Parent=StarterPlayer:WaitForChild("StarterPlayerScripts")
local ok,result=pcall(function()
 return StudioTestService:ExecuteMultiplayerTestAsync(2,"mutation-multiplayer")
end)
print("SF_MUTATION_MP_RESULT ok="..tostring(ok).." result="..tostring(result))
if not ok or result~="PASS:mutation_multiplayer" then error("multiplayer failure: "..tostring(result)) end
print("SF_MUTATION_MP_PASS")
