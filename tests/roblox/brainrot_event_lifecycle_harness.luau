-- Accelerated QA-only test: no production timing or game files are changed.
print("SF_EVENT_PROBE_BEGIN")
local StudioTestService = game:GetService("StudioTestService")
local ServerScriptService = game:GetService("ServerScriptService")
local test = Instance.new("Script")
test.Name = "SFEventLifecycleTest"
test.Source = [==[
local Players = game:GetService("Players")
local StudioTestService = game:GetService("StudioTestService")
local function fail(message)
    warn("SF_EVENT_FAIL " .. message)
    StudioTestService:EndTest("FAIL:" .. message)
end
local deadline = os.clock() + 18
local player
while os.clock() < deadline do
    player = Players:GetPlayers()[1]
    if player and player:GetAttribute("Snackquake") ~= nil then break end
    task.wait(0.1)
end
if not player then fail("no_player") return end
local arena = workspace:FindFirstChild("BrainrotRushArena")
if not arena then fail("no_arena") return end
local sawCap, sawRefill, sawEvent, sawEnd = false, false, false, false
local removedOne = false
local maxSeen = 0
local function orbs()
    local n, first = 0, nil
    for _, item in ipairs(arena:GetChildren()) do
        if item:IsA("BasePart") and string.find(item.Name, " Brainrot", 1, true) then
            n += 1
            first = first or item
        end
    end
    return n, first
end
while os.clock() < deadline do
    local count, first = orbs()
    maxSeen = math.max(maxSeen, count)
    if count > 12 then fail("orb_cap_exceeded_" .. count) return end
    if count == 12 then sawCap = true end
    if sawCap and not removedOne and first then
        first:Destroy()
        removedOne = true
        print("SF_EVENT_CHECK forced_cleanup PASS")
    elseif removedOne and count == 12 then
        sawRefill = true
    end
    local active = player:GetAttribute("Snackquake")
    if active == true then sawEvent = true end
    if sawEvent and active == false then sawEnd = true end
    if sawCap and sawRefill and sawEvent and sawEnd then break end
    task.wait(0.1)
end
if not sawCap then fail("orb_cap_never_reached") return end
if not sawRefill then fail("orb_did_not_refill") return end
if not sawEvent then fail("snackquake_did_not_start") return end
if not sawEnd then fail("snackquake_did_not_end") return end
print("SF_EVENT_SERVER_PASS cap=12 max_seen=" .. maxSeen .. " refill=true event_start=true event_end=true")
StudioTestService:EndTest("PASS:event_lifecycle")
]==]
test.Parent = ServerScriptService
local ok, result = pcall(function()
    return StudioTestService:ExecuteMultiplayerTestAsync(2, "brainrot-accelerated-event-lifecycle")
end)
print("SF_EVENT_PROBE_RESULT ok=" .. tostring(ok) .. " result=" .. tostring(result))
if not ok or result ~= "PASS:event_lifecycle" then
    error("Brainrot event QA failed: " .. tostring(result))
end
print("SF_EVENT_PROBE_PASS")
