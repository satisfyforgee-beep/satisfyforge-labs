local RunService = game:GetService("RunService")
if not RunService:IsStudio() then
    return
end

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local report = Instance.new("Folder")
report.Name = "SnackquakeStudioSmoke"
report.Parent = ReplicatedStorage

local passed = 0
local failed = 0
local messages = {}

local function check(label, condition, detail)
    if condition then
        passed = passed + 1
        messages[#messages + 1] = "PASS | " .. label
    else
        failed = failed + 1
        messages[#messages + 1] = "FAIL | " .. label .. (detail and (" | " .. detail) or "")
    end
end

local function countNamed(parent, name)
    local total = 0
    for _, child in ipairs(parent:GetChildren()) do
        if child.Name == name then
            total = total + 1
        end
    end
    return total
end

task.wait(4)

local shared = ReplicatedStorage:FindFirstChild("SnackquakeShared")
check("shared folder exists", shared ~= nil)

local config
if shared and shared:FindFirstChild("Config") then
    local ok, value = pcall(require, shared.Config)
    check("Config module loads", ok, ok and nil or tostring(value))
    if ok then
        config = value
    end
else
    check("Config module exists", false)
end

check("Action RemoteEvent exists", shared and shared:FindFirstChild("Action") and shared.Action:IsA("RemoteEvent"))
check("RoundState folder exists", shared and shared:FindFirstChild("RoundState") and shared.RoundState:IsA("Folder"))

local world = workspace:FindFirstChild("SnackquakeWorld")
check("runtime world replaced editor preview", world ~= nil and workspace:FindFirstChild("SnackquakeEditorPreview") == nil)
check("rescue chute exists", world and world:FindFirstChild("RescueChute") ~= nil)
check("15 rescue spots exist", world and countNamed(world, "RescueSpot") == 15,
    world and ("found " .. countNamed(world, "RescueSpot")) or "world missing")
check("starter golden beacon exists", world and world:FindFirstChild("StarterBeacon") ~= nil)
check("bright rescue runway exists", world and countNamed(world, "RescueRunway") == 4)
check("6 high-ground refuges exist", world and countNamed(world, "BlueRefuge") == 6,
    world and ("found " .. countNamed(world, "BlueRefuge")) or "world missing")
check("creature and disaster folders exist", world and world:FindFirstChild("Creatures") and world:FindFirstChild("Disasters"))

if config then
    check("8 original creature definitions", #config.Creatures == 8, "found " .. tostring(#config.Creatures))
    check("3 disaster definitions", #config.Events == 3, "found " .. tostring(#config.Events))
    check("72-second action round", config.RoundSeconds == 72, "found " .. tostring(config.RoundSeconds))
    check("first disaster warning by 22 seconds", config.WarningAt == 22 and config.PanicAt == 29)
    check("golden reward and combo configured", config.GoldenBonusFizz == 25 and config.ComboWindowSeconds == 24)
    check("upgrade costs are 50/120/240", config.SpeedCosts[1] == 50 and config.SpeedCosts[2] == 120 and config.SpeedCosts[3] == 240)
end

local roundState = shared and shared:FindFirstChild("RoundState")
check("round phase initialized", roundState and type(roundState:GetAttribute("Phase")) == "string")
check("round timer initialized", roundState and type(roundState:GetAttribute("EndsAt")) == "number")

local summary = string.format("Snackquake Studio smoke test: %d passed, %d failed", passed, failed)
report:SetAttribute("Passed", passed)
report:SetAttribute("Failed", failed)
report:SetAttribute("Summary", summary)

for _, message in ipairs(messages) do
    print("[Snackquake Smoke] " .. message)
end

if failed == 0 then
    print("[Snackquake Smoke] " .. summary)
else
    warn("[Snackquake Smoke] " .. summary)
end
