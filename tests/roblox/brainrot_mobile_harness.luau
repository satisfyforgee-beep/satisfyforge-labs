print('SF_MOBILE_GATE_BEGIN')
local StudioTestService = game:GetService('StudioTestService')
local Simulator = game:GetService('StudioDeviceSimulatorService')
local ServerScriptService = game:GetService('ServerScriptService')
local StarterPlayer = game:GetService('StarterPlayer')
local ReplicatedStorage = game:GetService('ReplicatedStorage')

local resultEvent = Instance.new('RemoteEvent')
resultEvent.Name = 'SFMobileGateResult'
resultEvent.Parent = ReplicatedStorage
local caseValue = Instance.new('StringValue')
caseValue.Name = 'SFMobileGateCase'
caseValue.Parent = ReplicatedStorage

local serverTest = Instance.new('Script')
serverTest.Name = 'SFMobileGateServerTest'
serverTest.Source = [==[
local StudioTestService = game:GetService('StudioTestService')
local ReplicatedStorage = game:GetService('ReplicatedStorage')
local ev = ReplicatedStorage:WaitForChild('SFMobileGateResult')
local done = false
ev.OnServerEvent:Connect(function(player, ok, detail)
    if done then return end
    done = true
    print('SF_MOBILE_GATE_SERVER ' .. tostring(ok) .. ' ' .. tostring(detail))
    StudioTestService:EndTest((ok and 'PASS:' or 'FAIL:') .. tostring(detail))
end)
task.delay(25, function()
    if not done then StudioTestService:EndTest('FAIL:client_timeout') end
end)
]==]
serverTest.Parent = ServerScriptService

local clientTest = Instance.new('LocalScript')
clientTest.Name = 'SFMobileGateClientTest'
clientTest.Source = [==[
local Players = game:GetService('Players')
local ReplicatedStorage = game:GetService('ReplicatedStorage')
local player = Players.LocalPlayer
local ev = ReplicatedStorage:WaitForChild('SFMobileGateResult')
local caseName = ReplicatedStorage:WaitForChild('SFMobileGateCase').Value
local function finish(ok, msg)
    print('SF_MOBILE_GATE_CLIENT ' .. tostring(ok) .. ' ' .. caseName .. ':' .. msg)
    ev:FireServer(ok, caseName .. ':' .. msg)
end
local gui = player:WaitForChild('PlayerGui'):WaitForChild('BrainrotRushHUD', 15)
if not gui then finish(false, 'hud_missing') return end
local top = gui:FindFirstChild('TopBar')
if not top then finish(false, 'topbar_missing') return end
local hint
for _, d in ipairs(gui:GetDescendants()) do
    if d:IsA('TextLabel') and string.find(d.Text, 'Collect glowing Brainrot', 1, true) then hint = d break end
end
if not hint then finish(false, 'hint_missing') return end
task.wait(0.8)
local viewport = workspace.CurrentCamera.ViewportSize
local portrait = string.find(caseName, 'portrait', 1, true) ~= nil
print('SF_MOBILE_GATE_VIEW ' .. caseName .. ' viewport=' .. viewport.X .. 'x' .. viewport.Y)
if portrait and viewport.Y <= viewport.X then finish(false, 'portrait_shape_wrong') return end
if not portrait and viewport.X <= viewport.Y then finish(false, 'landscape_shape_wrong') return end
local function inside(obj)
    local p, s = obj.AbsolutePosition, obj.AbsoluteSize
    return p.X >= -1 and p.Y >= -1 and p.X + s.X <= viewport.X + 1 and p.Y + s.Y <= viewport.Y + 1
end
if not inside(top) then finish(false, 'topbar_offscreen') return end
if not inside(hint) then finish(false, 'hint_offscreen') return end
if top.AbsolutePosition.Y + top.AbsoluteSize.Y >= hint.AbsolutePosition.Y then finish(false, 'top_hint_overlap') return end
for _, name in ipairs({'Brainrot','Level','Collected','Rebirths','Combo'}) do
    local label = top:FindFirstChild(name)
    if not label then finish(false, 'missing_' .. name) return end
    if label.AbsoluteSize.X < 35 or label.AbsoluteSize.Y < 30 then finish(false, 'stat_too_small_' .. name) return end
    if not inside(label) then finish(false, 'stat_offscreen_' .. name) return end
end
finish(true, 'bounds_ok_' .. math.floor(viewport.X) .. 'x' .. math.floor(viewport.Y))
]==]
clientTest.Parent = StarterPlayer.StarterPlayerScripts

local cases = {
    {name='iphone16_portrait', device='iphone_16', width=393, height=852},
    {name='iphone16_landscape', device='iphone_16', width=852, height=393},
    {name='galaxyA06_portrait', device='samsung_galaxy_a06', width=360, height=800},
    {name='galaxyA06_landscape', device='samsung_galaxy_a06', width=800, height=360},
}
for _, c in ipairs(cases) do
    caseValue.Value = c.name
    Simulator:SetDeviceAsync(c.device)
    Simulator:SetOrientationAsync(Enum.ScreenOrientation.LandscapeLeft)
    Simulator:SetResolutionAsync(c.width, c.height)
    Simulator:SetScalingModeAsync(Enum.DeviceSimulatorScalingMode.FitToWindow)
    task.wait(0.25)
    print('SF_MOBILE_GATE_HOST ' .. c.name .. ' resolution=' .. tostring(Simulator:GetResolutionAsync()))
    local ok, result = pcall(function()
        return StudioTestService:ExecutePlayModeAsync(c.name)
    end)
    print('SF_MOBILE_GATE_RESULT ' .. c.name .. ' ok=' .. tostring(ok) .. ' result=' .. tostring(result))
    local expected = 'PASS:' .. c.name .. ':bounds_ok_'
    if not ok or not string.find(tostring(result), expected, 1, true) then
        error('mobile gate failed ' .. c.name .. ': ' .. tostring(result))
    end
end
pcall(function() Simulator:StopSimulationAsync() end)
print('SF_MOBILE_GATE_PASS')
