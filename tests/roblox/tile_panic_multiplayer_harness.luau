-- Two-client behavior check: leaving the tile arena cannot earn a survival win.
local StudioTestService = game:GetService("StudioTestService")
local ServerScriptService = game:GetService("ServerScriptService")
print("SF_TILE_MP_BEGIN")
local test = Instance.new("Script")
test.Name = "SFTilePanicBoundaryTest"
test.Source = [==[
local Players = game:GetService("Players")
local StudioTestService = game:GetService("StudioTestService")
local function waitFor(fn, timeout)
 local deadline = os.clock() + timeout
 while os.clock() < deadline do
  local ok, value = pcall(fn)
  if ok and value then return value end
  task.wait(.1)
 end
 return nil
end
local function fail(reason)
 warn("SF_TILE_MP_FAIL " .. reason)
 StudioTestService:EndTest("FAIL:" .. reason)
end
local players = waitFor(function()
 local list = Players:GetPlayers()
 if #list >= 2 then return list end
end, 40)
if not players then fail("missing_two_clients") return end
local a,b = players[1],players[2]
local function root(p)
 return p.Character and p.Character:FindFirstChild("HumanoidRootPart")
end
local ready = waitFor(function()
 local r1,r2=root(a),root(b)
 if not r1 or not r2 then return false end
 local function inArena(r)
  local p=r.Position
  return math.abs(p.X)<=32 and math.abs(p.Z)<=32 and p.Y>7
 end
 return inArena(r1) and inArena(r2)
end, 25)
if not ready then fail("round_did_not_start_with_two_players") return end
local ra,rb=root(a),root(b)
ra.Anchored=true
rb.Anchored=true
local initialB=rb.Position
ra.CFrame=CFrame.new(25,15,-55)
local kicked=waitFor(function()
 local pos=ra.Position
 return math.abs(pos.X)<1 and math.abs(pos.Z+55)<1
end, 4)
if not kicked then fail("lobby_escape_not_eliminated") return end
if math.abs(rb.Position.X-initialB.X)>1 or math.abs(rb.Position.Z-initialB.Z)>1 then
 fail("other_player_displaced") return
end
print("SF_TILE_MP_CHECK lobby_escape_eliminated PASS")
print("SF_TILE_MP_CHECK other_player_unchanged PASS")
StudioTestService:EndTest("PASS:tile_panic_boundary")
]==]
test.Parent = ServerScriptService
local ok, result = pcall(function()
 return StudioTestService:ExecuteMultiplayerTestAsync(2, "tile-panic-boundary")
end)
print("SF_TILE_MP_RESULT ok="..tostring(ok).." result="..tostring(result))
if not ok or result ~= "PASS:tile_panic_boundary" then
 error("Tile Panic multiplayer boundary regression failed: "..tostring(result))
end
print("SF_TILE_MP_PASS")
