-- Real two-player Roblox Studio gameplay: golden pickup -> bank -> timed combo.
local StudioTestService=game:GetService("StudioTestService")
local ServerScriptService=game:GetService("ServerScriptService")
local StarterPlayer=game:GetService("StarterPlayer")
print("SF_SNACK_RUSH_BEGIN")
local server=Instance.new("Script"); server.Name="SFSnackRushServer"
server.Source=[==[
local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local StudioTestService=game:GetService("StudioTestService")
local Data=require(game:GetService("ServerScriptService"):WaitForChild("SnackquakeServer"):WaitForChild("PlayerData"))
local function waitFor(fn,seconds)
 local deadline=os.clock()+seconds
 while os.clock()<deadline do
  local ok,value=pcall(fn)
  if ok and value then return value end
  task.wait(.1)
 end
 return nil
end
local function fail(why)
 warn("SF_SNACK_RUSH_FAIL "..why)
 StudioTestService:EndTest("FAIL:"..why)
end
local players=waitFor(function()
 local list=Players:GetPlayers()
 if #list==2 and list[1]:GetAttribute("SFReady") and list[2]:GetAttribute("SFReady") then return list end
end,35)
if not players then fail("players_not_ready") return end
local p1,p2=players[1],players[2]
local rec1,rec2=Data.get(p1),Data.get(p2)
if not rec1 or not rec2 or rec1.canSave or rec2.canSave then fail("unsafe_data_mode") return end
rec1.profile.fizz=0; rec2.profile.fizz=0
local world=workspace:WaitForChild("SnackquakeWorld",10)
local creatures=world and world:WaitForChild("Creatures",10)
local bank=world and world:WaitForChild("RescueChute",10)
if not creatures or not bank then fail("missing_world") return end
local channel=Instance.new("RemoteEvent"); channel.Name="SFSnackRushProbe"; channel.Parent=ReplicatedStorage
local replies={}
channel.OnServerEvent:Connect(function(p,token,ok,detail)
 replies[p]=replies[p] or {}; replies[p][token]={ok=ok,detail=detail}
end)
local function trigger(p,part,token)
 local char=p.Character
 if not char then return false,"no_character" end
 char:PivotTo(CFrame.new(part.Position+Vector3.new(0,3,0)))
 task.wait(.45)
 channel:FireClient(p,token,part)
 local answer=waitFor(function() return replies[p] and replies[p][token] end,8)
 return answer and answer.ok,answer and answer.detail
end
local golden=waitFor(function()
 for _,model in ipairs(creatures:GetChildren()) do
  if model:FindFirstChild("GoldenRescueGlow") then return model.PrimaryPart end
 end
end,12)
if not golden then fail("no_golden_creature") return end
local ok,detail=trigger(p1,golden,"golden_pickup")
if not ok then fail("golden_prompt_"..tostring(detail)) return end
if not waitFor(function() return (p1:GetAttribute("SFCarry") or "")~="" end,4) then fail("golden_not_carried") return end
print("SF_SNACK_RUSH_CHECK golden_pickup PASS")
task.wait(1.2)
ok,detail=trigger(p1,bank,"golden_bank")
if not ok then fail("bank_prompt_"..tostring(detail)) return end
if not waitFor(function() return rec1.profile.rescues==1 end,4) then fail("golden_not_banked") return end
if rec1.profile.fizz<35 or rec2.profile.fizz~=0 or p1:GetAttribute("SFCombo")~=1 then
 fail("golden_reward_or_isolation fizz="..rec1.profile.fizz.." other="..rec2.profile.fizz.." combo="..tostring(p1:GetAttribute("SFCombo"))) return
end
print("SF_SNACK_RUSH_CHECK golden_reward PASS")
local firstFizz=rec1.profile.fizz
local regular=waitFor(function()
 for _,model in ipairs(creatures:GetChildren()) do
  if model.PrimaryPart and not model:FindFirstChild("GoldenRescueGlow") then
   if (model.PrimaryPart.Position-bank.Position).Magnitude<45 then return model.PrimaryPart end
  end
 end
end,6)
if not regular then fail("no_regular_creature") return end
ok,detail=trigger(p1,regular,"regular_pickup")
if not ok then fail("regular_prompt_"..tostring(detail)) return end
if not waitFor(function() return (p1:GetAttribute("SFCarry") or "")~="" end,4) then fail("regular_not_carried") return end
task.wait(1.2)
ok,detail=trigger(p1,bank,"regular_bank")
if not ok then fail("second_bank_prompt_"..tostring(detail)) return end
if not waitFor(function() return rec1.profile.rescues==2 end,4) then fail("regular_not_banked") return end
if p1:GetAttribute("SFCombo")~=2 or rec1.profile.fizz<firstFizz+14 or rec2.profile.rescues~=0 then
 fail("combo_or_isolation combo="..tostring(p1:GetAttribute("SFCombo")).." fizz="..rec1.profile.fizz) return
end
print("SF_SNACK_RUSH_CHECK combo_bonus PASS")
print("SF_SNACK_RUSH_SERVER_PASS golden=true combo=2 other_player_unaffected=true")
StudioTestService:EndTest("PASS:snackquake_rescue_rush")
]==]
server.Parent=ServerScriptService
local client=Instance.new("LocalScript"); client.Name="SFSnackRushClient"
client.Source=[==[
local channel=game:GetService("ReplicatedStorage"):WaitForChild("SFSnackRushProbe",20)
channel.OnClientEvent:Connect(function(token,part)
 local ok,err=pcall(function()
  assert(part and part.Parent,"part missing")
  local prompt=part:FindFirstChildOfClass("ProximityPrompt")
  assert(prompt,"prompt missing")
  prompt:InputHoldBegin()
  task.wait(math.max(.35,prompt.HoldDuration+.2))
  prompt:InputHoldEnd()
 end)
 channel:FireServer(token,ok,ok and "ok" or tostring(err))
end)
]==]
client.Parent=StarterPlayer:WaitForChild("StarterPlayerScripts")
local ok,result=pcall(function()
 return StudioTestService:ExecuteMultiplayerTestAsync(2,"snackquake-golden-combo")
end)
print("SF_SNACK_RUSH_RESULT ok="..tostring(ok).." result="..tostring(result))
if not ok or result~="PASS:snackquake_rescue_rush" then
 error("Snackquake golden combo test failed: "..tostring(result))
end
print("SF_SNACK_RUSH_PASS")
