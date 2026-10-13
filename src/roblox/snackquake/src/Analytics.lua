local Service=game:GetService("AnalyticsService")
local RunService=game:GetService("RunService")
local A={}; local warned=false
local function call(fn)
    if RunService:IsStudio() then return end
    local ok=pcall(fn)
    if not ok and not warned then warned=true; warn("Snackquake: analytics unavailable in this session") end
end
function A.custom(player,name,value)
    call(function() Service:LogCustomEvent(player,name,value or 1) end)
end
function A.step(player,step,name)
    call(function() Service:LogOnboardingFunnelStepEvent(player,step,name) end)
end
function A.economy(player,amount,balance,sku)
    if amount==0 then return end
    call(function()
        Service:LogEconomyEvent(player,amount>0 and Enum.AnalyticsEconomyFlowType.Source or Enum.AnalyticsEconomyFlowType.Sink,
            "Fizz",math.abs(amount),balance,amount>0 and "Gameplay" or "Shop",sku)
    end)
end
return A
