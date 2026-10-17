local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
local UserInputService=game:GetService("UserInputService")
local TweenService=game:GetService("TweenService")
local player=Players.LocalPlayer
local Shared=ReplicatedStorage:WaitForChild("SnackquakeShared")
local C=require(Shared:WaitForChild("Config")); local Creatures=require(Shared:WaitForChild("Creatures"))
local Remote=Shared:WaitForChild("Action"); local state=Shared:WaitForChild("RoundState")
local palette={dark=Color3.fromRGB(20,26,44),card=Color3.fromRGB(33,42,64),lime=Color3.fromRGB(185,255,107),
    blue=Color3.fromRGB(105,211,255),pink=Color3.fromRGB(255,118,170),muted=Color3.fromRGB(185,197,218)}
local profile=nil; local cargo=""; local saveStatus="Loading progress..."; local dashReady=0; local calm=false
local gui=Instance.new("ScreenGui"); gui.Name="SnackquakeUI"; gui.ResetOnSpawn=false; gui.DisplayOrder=5
gui.ZIndexBehavior=Enum.ZIndexBehavior.Sibling; gui.Parent=player:WaitForChild("PlayerGui")
local function corner(obj,r)
    local c=Instance.new("UICorner"); c.CornerRadius=UDim.new(0,r or 14); c.Parent=obj
end
local function frame(parent,size,pos,color)
    local f=Instance.new("Frame"); f.Size=size; f.Position=pos; f.BackgroundColor3=color or palette.dark
    f.BorderSizePixel=0; f.Parent=parent; corner(f); return f
end
local function label(parent,text,size,pos,fontSize,color)
    local l=Instance.new("TextLabel"); l.Size=size; l.Position=pos; l.BackgroundTransparency=1
    l.Text=text; l.Font=Enum.Font.GothamBold; l.TextSize=fontSize or 16; l.TextColor3=color or Color3.new(1,1,1)
    l.TextWrapped=true; l.Parent=parent; return l
end
local function button(parent,text,size,pos,color,callback)
    local b=Instance.new("TextButton"); b.Size=size; b.Position=pos; b.BackgroundColor3=color or palette.card
    b.BorderSizePixel=0; b.Text=text; b.Font=Enum.Font.GothamBold; b.TextSize=14; b.TextColor3=Color3.new(1,1,1)
    b.TextWrapped=true; b.Parent=parent; corner(b,10); b.Activated:Connect(callback); return b
end
local function maxSize(obj,x,y)
    local c=Instance.new("UISizeConstraint"); c.MaxSize=Vector2.new(x,y); c.Parent=obj
end
local hud=frame(gui,UDim2.new(.92,0,0,86),UDim2.new(.5,0,0,9)); hud.AnchorPoint=Vector2.new(.5,0); maxSize(hud,780,86); hud.Name="CompactHUD"
local title=label(hud,"SNACKQUAKE RUSH",UDim2.new(.60,-8,0,25),UDim2.fromOffset(12,5),19,palette.lime); title.TextXAlignment=Enum.TextXAlignment.Left
title.TextScaled=true
local titleLimit=Instance.new("UITextSizeConstraint"); titleLimit.MinTextSize=12; titleLimit.MaxTextSize=19; titleLimit.Parent=title
local money=label(hud,"0 FIZZ",UDim2.new(.4,-16,0,25),UDim2.new(.6,0,0,5),18,palette.blue); money.TextXAlignment=Enum.TextXAlignment.Right
local roundLabel=label(hud,"Get ready to rescue!",UDim2.new(1,-22,0,23),UDim2.fromOffset(11,27),15)
local hint=label(hud,"Golden creature -> green chute -> survive!",UDim2.new(1,-22,0,22),UDim2.fromOffset(11,51),12,palette.muted)
local meter=frame(hud,UDim2.new(1,-24,0,5),UDim2.fromOffset(12,78),palette.card)
local meterFill=frame(meter,UDim2.fromScale(0,1),UDim2.fromScale(0,0),palette.lime)
local nav=frame(gui,UDim2.new(.92,0,0,34),UDim2.new(.5,0,0,103)); nav.AnchorPoint=Vector2.new(.5,0); nav.BackgroundTransparency=1; nav.Name="Navigation"; maxSize(nav,310,34)
local panel=frame(gui,UDim2.new(.92,0,.60,0),UDim2.fromScale(.5,.58)); panel.AnchorPoint=Vector2.new(.5,.5); maxSize(panel,740,520); panel.Visible=false
local panelTitle=label(panel,"COLLECTION",UDim2.new(1,-80,0,40),UDim2.fromOffset(16,8),22,palette.lime); panelTitle.TextXAlignment=Enum.TextXAlignment.Left
button(panel,"X",UDim2.fromOffset(40,36),UDim2.new(1,-51,0,10),palette.card,function() panel.Visible=false end)
local content=Instance.new("ScrollingFrame"); content.Name="Content"; content.Position=UDim2.fromOffset(12,57)
content.Size=UDim2.new(1,-24,1,-69); content.BackgroundTransparency=1; content.BorderSizePixel=0
content.ScrollBarThickness=4; content.AutomaticCanvasSize=Enum.AutomaticSize.Y; content.CanvasSize=UDim2.new(); content.Parent=panel
local openTab=""; local renderPanel
local saveLabel=label(gui,"",UDim2.new(.90,0,0,20),UDim2.new(.5,0,0,182),11,palette.muted)
saveLabel.AnchorPoint=Vector2.new(.5,0)
local function showTab(tab)
    if panel.Visible and openTab==tab then panel.Visible=false; return end
    openTab=tab; panel.Visible=true; content.CanvasPosition=Vector2.zero; renderPanel()
end
button(nav,"CREATURES",UDim2.new(.37,0,1,0),UDim2.fromScale(0,0),palette.card,function() showTab("collection") end)
button(nav,"UPGRADES",UDim2.new(.34,0,1,0),UDim2.fromScale(.39,0),palette.card,function() showTab("upgrades") end)
button(nav,"HELP",UDim2.new(.25,0,1,0),UDim2.fromScale(.75,0),palette.card,function() showTab("help") end)
local toast=frame(gui,UDim2.new(.86,0,0,66),UDim2.fromScale(.5,.77)); toast.AnchorPoint=Vector2.new(.5,.5); maxSize(toast,650,66); toast.Visible=false
local toastText=label(toast,"",UDim2.new(1,-24,1,-12),UDim2.fromOffset(12,6),17)
local toastVersion=0
local function notify(text,tone)
    toastVersion=toastVersion+1; local mine=toastVersion
    toastText.Text=text; toastText.TextColor3=tone=="danger" and palette.pink or tone=="good" and palette.lime or Color3.new(1,1,1)
    toast.BackgroundTransparency=.05; toast.Visible=true
    task.delay(4.4,function() if toastVersion==mine then toast.Visible=false end end)
end
local dash=button(gui,"DASH\nQ / SHIFT",UDim2.fromOffset(76,68),UDim2.fromScale(.97,.67),palette.card,function() Remote:FireServer("dash") end)
dash.AnchorPoint=Vector2.new(1,1); dash.Name="DashButton"
local votes=frame(gui,UDim2.new(.92,0,0,82),UDim2.fromScale(.5,.69)); votes.AnchorPoint=Vector2.new(.5,.5); maxSize(votes,740,82); votes.Visible=false
label(votes,"CHOOSE THE NEXT SNACKQUAKE",UDim2.new(1,0,0,23),UDim2.fromOffset(0,5),13,palette.lime)
for i,e in ipairs(C.Events) do
    button(votes,e.name,UDim2.new(1/3,-10,0,39),UDim2.new((i-1)/3,5,0,34),palette.card,function() Remote:FireServer("vote",e.id) end)
end
-- Always-visible objective: a player should know what to do within two seconds.
local objective=frame(gui,UDim2.new(.70,0,0,38),UDim2.new(.5,0,0,142),palette.card)
objective.AnchorPoint=Vector2.new(.5,0); maxSize(objective,620,38); objective.Name="RescueObjective"
local objectiveText=label(objective,"1/2  FIND A GOLDEN CREATURE",UDim2.new(1,-14,1,0),UDim2.fromOffset(7,0),14,palette.lime)
local dangerBar=frame(gui,UDim2.new(.70,0,0,35),UDim2.new(.5,0,0,208),palette.pink)
dangerBar.AnchorPoint=Vector2.new(.5,0); maxSize(dangerBar,620,35); dangerBar.Visible=false; dangerBar.Name="DisasterAlert"
local dangerText=label(dangerBar,"DANGER! GET TO HIGH GROUND!",UDim2.new(1,-14,1,0),UDim2.fromOffset(7,0),13,palette.dark)
local function preview(parent,spec,evolution,seen)
    local v=Instance.new("ViewportFrame"); v.Size=UDim2.fromOffset(68,80); v.Position=UDim2.fromOffset(4,6)
    v.BackgroundTransparency=1; v.Ambient=Color3.fromRGB(200,200,200); v.LightColor=Color3.new(1,1,1); v.Parent=parent
    local camera=Instance.new("Camera"); camera.CFrame=CFrame.lookAt(Vector3.new(4,2,-7),Vector3.new(0,0,0)); camera.Parent=v; v.CurrentCamera=camera
    local worldModel=Instance.new("WorldModel"); worldModel.Parent=v
    local m=Creatures.make(spec,worldModel,1,evolution)
    if not seen then for _,p in ipairs(m:GetDescendants()) do if p:IsA("BasePart") then p.Color=Color3.fromRGB(60,71,89); p.Material=Enum.Material.SmoothPlastic end end end
end
renderPanel=function()
    local previousScroll=content.CanvasPosition
    content:ClearAllChildren()
    if openTab=="collection" then
        panelTitle.Text="YOUR CREATURES"
        local grid=Instance.new("UIGridLayout"); grid.CellSize=content.AbsoluteSize.X<420 and UDim2.new(1,-8,0,142) or UDim2.new(.5,-6,0,142); grid.CellPadding=UDim2.fromOffset(8,8); grid.SortOrder=Enum.SortOrder.LayoutOrder; grid.Parent=content
        for i,spec in ipairs(C.Creatures) do
            local seen=profile and profile.seen[spec.id]; local level=profile and profile.evolution[spec.id] or 0
            local count=profile and profile.copies[spec.id] or 0
            local card=frame(content,UDim2.new(),UDim2.new(),palette.card); card.LayoutOrder=i
            preview(card,spec,level,seen)
            label(card,seen and spec.name or "???",UDim2.new(1,-78,0,39),UDim2.fromOffset(74,7),14,seen and palette.lime or palette.muted)
            label(card,(seen and C.EvolutionNames[level+1] or spec.rarity).."\nCopies: "..count,UDim2.new(1,-78,0,39),UDim2.fromOffset(74,48),12,palette.muted)
            local equip=button(card,profile and profile.equipped==spec.id and "EQUIPPED" or "EQUIP",UDim2.new(.5,-8,0,35),UDim2.fromOffset(5,99),palette.dark,function() if seen then Remote:FireServer("equip",spec.id) end end)
            local fuse=button(card,level>=3 and "MEGA" or "EVOLVE: 3",UDim2.new(.5,-8,0,35),UDim2.new(.5,3,0,99),palette.dark,function() if seen then Remote:FireServer("fuse",spec.id) end end)
            equip.TextSize=11; fuse.TextSize=11
            if not seen then equip.TextColor3=palette.muted; fuse.TextColor3=palette.muted end
        end
    elseif openTab=="upgrades" then
        panelTitle.Text="EARNED UPGRADES"
        local level=profile and profile.speed or 0; local cost=C.SpeedCosts[level+1]
        label(content,"SPEED  "..level.." / 3",UDim2.new(1,-20,0,38),UDim2.fromOffset(10,10),23,palette.blue)
        label(content,"Move faster between the arena and the rescue chute.\nEach level adds 2 movement speed.",UDim2.new(1,-20,0,75),UDim2.fromOffset(10,52),16,palette.muted)
        button(content,cost and "UPGRADE: "..cost.." FIZZ" or "MAX LEVEL",UDim2.new(1,-40,0,54),UDim2.fromOffset(20,136),palette.card,function() if cost then Remote:FireServer("upgrade") end end)
        label(content,"Fizz comes from rescues and active round bonuses.\nEvolve companions in COLLECTION with 3 duplicate copies.",UDim2.new(1,-20,0,83),UDim2.fromOffset(10,204),15,palette.muted)
        label(content,"DAILY STREAK: "..(profile and profile.loginStreak or 0).." / 7\nDAILY RESCUES: "..(profile and profile.missionRescues or 0).." / "..C.DailyRescueGoal.." (+"..C.DailyMissionFizz.." Fizz)",UDim2.new(1,-20,0,58),UDim2.fromOffset(10,290),15,palette.lime)
        if C.FounderGlowPassId>0 then
            button(content,player:GetAttribute("SFFounderGlow") and "FOUNDER GLOW OWNED" or "FOUNDER GLOW - VIEW PASS",UDim2.new(1,-40,0,43),UDim2.fromOffset(20,420),palette.card,function()
                if not player:GetAttribute("SFFounderGlow") then Remote:FireServer("founderPass") end
            end)
        end
        label(content,"BEST ROUND: "..(profile and profile.best or 0).." RESCUES\nCLEAN ESCAPES: "..(profile and profile.wins or 0),UDim2.new(1,-20,0,54),UDim2.fromOffset(10,356),15,palette.blue)
    else
        panelTitle.Text="RESCUE FIELD GUIDE"
        local text="1. Walk to a creature. Press E, gamepad X, or tap its prompt.\n\n2. Carry it to the green RESCUE chute. Your collection and Fizz are banked there.\n\n3. Read the disaster warning. Blue platforms and the lobby are safe from rising sauce. Dodge toaster lanes and popcorn circles.\n\n4. Rescue duplicates, evolve companions, and vote for the next disaster. Use Q / Shift or the DASH button to escape."
        label(content,text,UDim2.new(1,-22,0,250),UDim2.fromOffset(11,0),15,palette.muted)
        button(content,calm and "CALM MOTION: ON" or "CALM MOTION: OFF",UDim2.new(1,-30,0,42),UDim2.fromOffset(15,263),palette.card,function() calm=not calm; renderPanel() end)
        label(content,saveStatus,UDim2.new(1,-20,0,46),UDim2.fromOffset(10,318),13,palette.blue)
    end
    content.CanvasPosition=previousScroll
end
Remote.OnClientEvent:Connect(function(message)
    if type(message)~="table" then return end
    if message.kind=="snapshot" then
        profile=message.profile; cargo=message.carrying; saveStatus=message.saveStatus; dashReady=message.dashReadyAt or 0
        local amount=profile.fizz
        local shown=amount>=1000000 and string.format("%.1fM",amount/1000000) or amount>=10000 and string.format("%.1fK",amount/1000) or tostring(amount)
        money.Text=shown.." FIZZ"
        saveLabel.Text=saveStatus=="Cloud save ready" and "" or saveStatus
        if panel.Visible then renderPanel() end
    elseif message.kind=="toast" then notify(message.text,message.tone)
    elseif message.kind=="result" then
        notify("ROUND COMPLETE: "..message.rescues.." rescued | +"..message.bonus.." Fizz"..(message.clean and " | CLEAN ESCAPE!" or ""),"good")
    end
end)
UserInputService.InputBegan:Connect(function(input,processed)
    if processed then return end
    if input.KeyCode==Enum.KeyCode.Q or input.KeyCode==Enum.KeyCode.LeftShift or input.KeyCode==Enum.KeyCode.ButtonY then Remote:FireServer("dash") end
    if input.KeyCode==Enum.KeyCode.B then showTab("collection") end
end)
local companions={}; local renderFolder=Instance.new("Folder"); renderFolder.Name="SnackquakeLocalCompanions"; renderFolder.Parent=workspace
local tickAccumulator=0
RunService.RenderStepped:Connect(function(dt)
    local time=workspace:GetServerTimeNow(); local phase=state:GetAttribute("Phase") or "IDLE"
    local left=math.max(0,math.ceil((state:GetAttribute("EndsAt") or 0)-time))
    local danger=state:GetAttribute("EventName") or "SNACKQUAKE"
    local combo=player:GetAttribute("SFCombo") or 0
    if phase=="BREAK" then roundLabel.Text="NEXT ROUND IN "..left.."s - VOTE BELOW"
    elseif phase=="PANIC" then roundLabel.Text=danger.."  |  "..left.."s"; roundLabel.TextColor3=palette.pink
    elseif phase=="WARNING" then roundLabel.Text=danger.." IN "..math.max(0,left-(C.RoundSeconds-C.PanicAt)).."s"; roundLabel.TextColor3=palette.pink
    else roundLabel.Text="ROUND "..(state:GetAttribute("Round") or 0).."  |  RESCUE RUN  |  "..left.."s"; roundLabel.TextColor3=Color3.new(1,1,1) end
    votes.Visible=phase=="BREAK" and not panel.Visible
    dash.Visible=phase~="BREAK"
    objective.Visible=not panel.Visible and phase~="BREAK"
    if cargo~="" then
        objectiveText.Text="2/2  BANK YOUR CREATURE AT THE GREEN CHUTE!"
        objectiveText.TextColor3=palette.lime
    elseif (profile and profile.rescues or 0)==0 then
        objectiveText.Text="1/2  GRAB THE GLOWING GOLDEN CREATURE!"
        objectiveText.TextColor3=palette.lime
    else
        objectiveText.Text=combo>1 and ("COMBO x"..combo.."! RESCUE AGAIN FOR BONUS FIZZ") or "RESCUE MORE CREATURES! GOLD = BONUS FIZZ"
        objectiveText.TextColor3=palette.blue
    end
    dangerBar.Visible=(phase=="WARNING" or phase=="PANIC") and not panel.Visible
    if phase=="PANIC" then
        dangerText.Text="DISASTER NOW! "..(state:GetAttribute("Hint") or "DODGE!")
    else
        dangerText.Text=danger.." IN "..math.max(0,left-(C.RoundSeconds-C.PanicAt)).."s! PREPARE!"
    end
    local frenzy=time<(state:GetAttribute("FrenzyUntil") or 0)
    local charge=state:GetAttribute("TeamCharge") or 0; local goal=math.max(1,state:GetAttribute("TeamGoal") or 4)
    meterFill.Size=UDim2.fromScale(frenzy and 1 or math.min(1,charge/goal),1)
    if cargo~="" and C.ById[cargo] then hint.Text="CARRYING "..C.ById[cargo].name.." -> GREEN RESCUE CHUTE"
    elseif frenzy then hint.Text="TEAM FRENZY: +50% rescue Fizz!"
    elseif phase=="PANIC" then hint.Text=state:GetAttribute("Hint") or "Dodge the disaster!"
    else hint.Text="Grab -> rescue -> evolve   |   Team frenzy: "..charge.." / "..goal end
    local cooldown=math.max(0,dashReady-time)
    dash.Text=cooldown>.1 and "DASH\n"..math.ceil(cooldown).."s" or (UserInputService.TouchEnabled and "DASH" or "DASH\nQ / SHIFT")
    tickAccumulator=tickAccumulator+dt
    if tickAccumulator<1/20 then return end
    tickAccumulator=0
    local living={}
    for _,other in ipairs(Players:GetPlayers()) do
        local root=other.Character and other.Character:FindFirstChild("HumanoidRootPart")
        local carry=other:GetAttribute("SFCarry") or ""; local id=carry~="" and carry or other:GetAttribute("SFEquipped")
        local evolution=carry~="" and 0 or (other:GetAttribute("SFEvolution") or 0)
        if root and id and C.ById[id] then
            living[other]=true
            local key=id..":"..evolution..":"..tostring(carry~="")..":"..tostring(frenzy)
            local entry=companions[other]
            if not entry or entry.key~=key then
                if entry then entry.model:Destroy() end
                local scale=(carry~="" and .62 or .65+evolution*.1)*(frenzy and 1.65 or 1)
                entry={key=key,model=Creatures.make(C.ById[id],renderFolder,scale,evolution)}; companions[other]=entry
            end
            local bob=calm and 0 or math.sin(time*3+other.UserId%20)*.17
            local cf=root.CFrame*CFrame.new(carry~="" and 0 or 2.7,carry~="" and 1.5+bob or -1+bob,carry~="" and -2.5 or 2.8)
            entry.model:PivotTo(cf)
        end
    end
    for other,entry in pairs(companions) do if not living[other] then entry.model:Destroy(); companions[other]=nil end end
end)
Remote:FireServer("sync")
player:GetAttributeChangedSignal("SFReady"):Connect(function() Remote:FireServer("sync") end)
task.spawn(function()
    while gui.Parent do task.wait(10); Remote:FireServer("sync") end
end)
