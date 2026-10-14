local Players=game:GetService("Players")
local ReplicatedStorage=game:GetService("ReplicatedStorage")
local RunService=game:GetService("RunService")
local Debris=game:GetService("Debris")
local MarketplaceService=game:GetService("MarketplaceService")
local Shared=ReplicatedStorage:WaitForChild("SnackquakeShared")
local C=require(Shared.Config); local R=require(Shared.Rules); local Creatures=require(Shared.Creatures)
local W=require(script.Parent.World); local Data=require(script.Parent.PlayerData); local Analytics=require(script.Parent.Analytics)
local world=W.build()
local Remote=Instance.new("RemoteEvent"); Remote.Name="Action"; Remote.Parent=Shared
local state=Instance.new("Folder"); state.Name="RoundState"; state.Parent=Shared
local tokens,carried,runtime,votes={},{},{},{}
local round=0; local phase="IDLE"; local activeEvent="sauce"; local teamCharge=0; local goal=4; local frenzyUntil=0
local closing=false; local tokenSerial=0
local ids={}; for _,e in ipairs(C.Events) do ids[#ids+1]=e.id end
local function now() return workspace:GetServerTimeNow() end
local function tell(player,message,tone)
    if player.Parent then Remote:FireClient(player,{kind="toast",text=message,tone=tone or "info"}) end
end
local function announce(message,tone) Remote:FireAllClients({kind="toast",text=message,tone=tone or "info"}) end
local function character(player)
    local char=player.Character; if not char then return nil end
    local root=char:FindFirstChild("HumanoidRootPart"); local hum=char:FindFirstChildOfClass("Humanoid")
    if not root or not hum or hum.Health<=0 then return nil end
    return root,hum
end
local function applyFounderGlow(player)
    local char=player.Character
    if not char then return end
    local existing=char:FindFirstChild("SnackquakeFounderGlow")
    if existing and runtime[player] and runtime[player].founderGlow then return end
    if existing then existing:Destroy() end
    if runtime[player] and runtime[player].founderGlow then
        local glow=Instance.new("Highlight")
        glow.Name="SnackquakeFounderGlow"
        glow.FillColor=Color3.fromRGB(195,118,255)
        glow.OutlineColor=Color3.fromRGB(115,255,223)
        glow.FillTransparency=.78
        glow.OutlineTransparency=.1
        glow.DepthMode=Enum.HighlightDepthMode.Occluded
        glow.Parent=char
    end
end
local function appearance(player)
    local rec=Data.get(player); if not rec then return end
    local p=rec.profile
    player:SetAttribute("SFEquipped",p.equipped); player:SetAttribute("SFEvolution",p.evolution[p.equipped] or 0)
    player:SetAttribute("SFCarry",carried[player] and carried[player].id or "")
    player:SetAttribute("SFFounderGlow",runtime[player] and runtime[player].founderGlow == true)
    applyFounderGlow(player)
    local _,hum=character(player)
    if hum then hum.WalkSpeed=18+p.speed*2-(carried[player] and 2 or 0) end
    local stats=player:FindFirstChild("leaderstats")
    if stats then stats.Fizz.Value=p.fizz; stats.Rescues.Value=p.rescues end
end
local function sync(player)
    local rec=Data.get(player); if not rec then return end
    appearance(player)
    if player.Parent then Remote:FireClient(player,{kind="snapshot",profile=R.copy(rec.profile),saveStatus=rec.status,
        carrying=carried[player] and carried[player].id or "",dashReadyAt=runtime[player] and runtime[player].dashReady or 0}) end
end
local function active() return phase=="HUNT" or phase=="WARNING" or phase=="PANIC" end
local function interactive(player,part,enabled)
    local rt=runtime[player]; local rec=Data.get(player); local root=character(player)
    if not rt or not rec or rec.closing or not root or not part.Parent then return false end
    if not R.canInteract((root.Position-part.Position).Magnitude,true,enabled,os.clock()-rt.lastPrompt) then return false end
    rt.lastPrompt=os.clock(); return true
end
local function setPhase(value,endsAt)
    phase=value; state:SetAttribute("Phase",value); state:SetAttribute("EndsAt",endsAt or 0)
    state:SetAttribute("Round",round); state:SetAttribute("EventId",activeEvent)
    state:SetAttribute("TeamGoal",goal); state:SetAttribute("TeamCharge",teamCharge); state:SetAttribute("FrenzyUntil",frenzyUntil)
    for _,e in ipairs(C.Events) do if e.id==activeEvent then state:SetAttribute("EventName",e.name); state:SetAttribute("Hint",e.hint) end end
end
local function drop(player)
    carried[player]=nil; appearance(player)
end
local function bounce(player,reason)
    local rt=runtime[player]; local root=character(player)
    if not rt or not root or now()<rt.immuneUntil then return end
    rt.immuneUntil=now()+2; rt.bounces=rt.bounces+1
    drop(player); player.Character:PivotTo(CFrame.new(math.random(-9,9),5,57))
    root.AssemblyLinearVelocity=Vector3.zero
    tell(player,reason.." Your banked collection is safe.","danger"); sync(player)
    Analytics.custom(player,"DisasterBounce",1)
end
local function clearTokens()
    for _,token in pairs(tokens) do if token.model.Parent then token.model:Destroy() end end
    tokens={}
end
local spawnToken
spawnToken=function(slot,expectedRound)
    if closing or round~=expectedRound or not active() or tokens[slot.index] then return end
    tokenSerial=tokenSerial+1
    local index
    if slot.row==1 then index=1+((slot.index+round)%2)
    elseif slot.row==2 then index=math.random(2,5)
    else index=math.random(4,8) end
    local spec=C.Creatures[index]
    local model=Creatures.make(spec,world.tokens,.85,0); model:PivotTo(CFrame.new(slot.position))
    local body=model.PrimaryPart
    local prompt=W.prompt(body,"RESCUE",spec.name.." | "..spec.value.." Fizz")
    local nameLabel=W.label(body,spec.name.."\n"..spec.rarity.." / "..spec.value.." Fizz",Color3.fromRGB(spec.accent[1],spec.accent[2],spec.accent[3]),190,48)
    nameLabel.Parent.MaxDistance=55
    local token={id=spec.id,model=model,slot=slot}; tokens[slot.index]=token
    prompt.Triggered:Connect(function(player)
        if not active() or tokens[slot.index]~=token or carried[player] then return end
        if not interactive(player,body,prompt.Enabled) then return end
        tokens[slot.index]=nil; prompt.Enabled=false
        carried[player]={id=spec.id,pickedAt=now(),distance=(slot.position-world.bank.Position).Magnitude}
        model:Destroy(); appearance(player); sync(player)
        local rt=runtime[player]
        if not rt.firstPickup then rt.firstPickup=true; Analytics.step(player,2,"FirstCreaturePickedUp") end
        tell(player,"Got "..spec.name.."! Return to the green rescue chute.","good")
        task.delay(C.RespawnSeconds,function() spawnToken(slot,expectedRound) end)
    end)
end
world.bankPrompt.Triggered:Connect(function(player)
    local cargo=carried[player]
    if not cargo or not active() or not interactive(player,world.bank,world.bankPrompt.Enabled) then return end
    if not R.canDeliver(now()-cargo.pickedAt,cargo.distance) then return end
    local rec=Data.get(player); local rt=runtime[player]
    if not rec or not rt then return end
    carried[player]=nil
    local reward,discovered=R.rescue(rec.profile,cargo.id,now()<frenzyUntil,C)
    if not reward then return end
    Data.changed(player); rt.deliveries=rt.deliveries+1
    local missionReward=R.dailyMission(rec.profile,math.floor(os.time()/86400),C)
    if missionReward>0 then tell(player,"DAILY RESCUE MISSION! +"..missionReward.." Fizz","good") end
    teamCharge=teamCharge+1
    if teamCharge>=goal then
        teamCharge=0; frenzyUntil=now()+12; state:SetAttribute("FrenzyUntil",frenzyUntil)
        announce("TEAM FRENZY! Huge companions + 50% rescue Fizz for 12 seconds!","good")
    end
    state:SetAttribute("TeamCharge",teamCharge)
    local spec=C.ById[cargo.id]
    tell(player,(discovered and "NEW! " or "RESCUED! ")..spec.name.."  +"..reward.." Fizz","good")
    Analytics.economy(player,reward,rec.profile.fizz,"CreatureRescue")
    if not rt.firstDeposit then
        rt.firstDeposit=true; Analytics.step(player,3,"FirstCreatureRescued")
        Analytics.custom(player,"SecondsToFirstRescue",math.floor(os.clock()-rec.joined))
    end
    sync(player)
end)
Remote.OnServerEvent:Connect(function(player,action,payload)
    if type(action)~="string" or #action>20 then return end
    local rt=runtime[player]; local rec=Data.get(player)
    if not rt or not rec or rec.closing then return end
    if os.clock()-rt.lastAction<.15 then return end
    rt.lastAction=os.clock()
    if action=="sync" then sync(player); return end
    if action=="founderPass" then
        if C.FounderGlowPassId>0 then
            MarketplaceService:PromptGamePassPurchase(player,C.FounderGlowPassId)
        end
        return
    end
    if action=="vote" then
        if phase~="BREAK" or type(payload)~="string" then return end
        for _,id in ipairs(ids) do if payload==id then votes[player.UserId]=id; tell(player,"Vote recorded","good"); return end end
        return
    end
    if action=="dash" then
        local root,hum=character(player)
        if not root or now()<rt.dashReady then return end
        rt.dashReady=now()+6
        local d=hum.MoveDirection.Magnitude>.1 and hum.MoveDirection.Unit or root.CFrame.LookVector
        root.AssemblyLinearVelocity=Vector3.new(d.X*62,math.max(8,root.AssemblyLinearVelocity.Y),d.Z*62)
        sync(player); return
    end
    if action=="upgrade" then
        local ok,result=R.upgrade(rec.profile,C)
        if ok then Data.changed(player); Analytics.economy(player,-result,rec.profile.fizz,"SpeedUpgrade"); tell(player,"Speed upgraded!","good")
        else tell(player,result,"info") end
        sync(player); return
    end
    if type(payload)~="string" or #payload>32 or not C.ById[payload] then return end
    if action=="fuse" then
        local ok,result=R.fuse(rec.profile,payload,C)
        if ok then Data.changed(player); tell(player,C.ById[payload].name.." evolved to "..result.."!","good"); Analytics.custom(player,"CreatureEvolved",1)
        else tell(player,result,"info") end
    elseif action=="equip" and rec.profile.seen[payload] then rec.profile.equipped=payload; Data.changed(player) end
    sync(player)
end)
MarketplaceService.PromptGamePassPurchaseFinished:Connect(function(player,passId,wasPurchased)
    if C.FounderGlowPassId<=0 or passId~=C.FounderGlowPassId or not wasPurchased then return end
    task.spawn(function()
        local ok,owns=pcall(function() return MarketplaceService:UserOwnsGamePassAsync(player.UserId,passId) end)
        if ok and owns and runtime[player] then
            runtime[player].founderGlow=true; appearance(player)
            tell(player,"Founder Glow equipped! Thanks for supporting Snackquake!","good")
        end
    end)
end)
local function onJoin(player)
    runtime[player]={lastPrompt=-10,lastAction=-10,dashReady=0,immuneUntil=now()+3,deliveries=0,bounces=0}
    local stats=Instance.new("Folder"); stats.Name="leaderstats"; stats.Parent=player
    for _,name in ipairs({"Fizz","Rescues"}) do local value=Instance.new("IntValue"); value.Name=name; value.Parent=stats end
    player.CharacterAdded:Connect(function(char)
        local hum=char:WaitForChild("Humanoid",10)
        if not hum then return end
        drop(player)
        applyFounderGlow(player)
        if runtime[player] then runtime[player].immuneUntil=now()+3 end
        hum.Died:Connect(function() drop(player); sync(player) end)
    end)
    local loaded=Data.load(player)
    if loaded then
        local award=R.dailyLogin(loaded.profile,math.floor(os.time()/86400),C)
        if award>0 then
            Data.changed(player)
            tell(player,"DAILY LOGIN! Day "..loaded.profile.loginStreak.." +"..award.." Fizz","good")
        end
    end
    if C.FounderGlowPassId > 0 then
        task.spawn(function()
            local ok,owns=pcall(function() return MarketplaceService:UserOwnsGamePassAsync(player.UserId,C.FounderGlowPassId) end)
            if ok and owns and runtime[player] then
                runtime[player].founderGlow=true; appearance(player)
            end
        end)
    end
    if not player.Parent then
        Data.save(player,true); Data.records[player]=nil; runtime[player]=nil; return
    end
    player:SetAttribute("SFReady",true); Analytics.step(player,1,"Joined")
    sync(player); tell(player,"Grab a creature, then bring it to the green chute. E / tap to rescue!","good")
end
Players.PlayerAdded:Connect(onJoin)
for _,player in ipairs(Players:GetPlayers()) do task.spawn(onJoin,player) end
Players.PlayerRemoving:Connect(function(player)
    local rec=Data.get(player)
    if rec then
        rec.closing=true; Analytics.custom(player,"SessionSeconds",math.floor(os.clock()-rec.joined)); Data.save(player,true)
        Data.records[player]=nil
    end
    carried[player]=nil; runtime[player]=nil; votes[player.UserId]=nil
end)
task.spawn(function()
    while not closing do
        task.wait(C.AutosaveSeconds)
        for _,player in ipairs(Players:GetPlayers()) do
            task.spawn(function() if Data.get(player) then Data.save(player,false); sync(player) end end)
        end
    end
end)
if not RunService:IsStudio() then
    game:BindToClose(function()
        closing=true; local pending=0
        for _,player in ipairs(Players:GetPlayers()) do
            if Data.get(player) then
                Data.get(player).closing=true; pending=pending+1
                task.spawn(function() Data.save(player,true); pending=pending-1 end)
            end
        end
        local deadline=os.clock()+25
        while pending>0 and os.clock()<deadline do task.wait(.1) end
    end)
end
local hazardObjects={}
local function resetHazards()
    for _,obj in ipairs(hazardObjects) do if obj.Parent then obj:Destroy() end end
    hazardObjects={}; world.sauce.Position=Vector3.new(0,-5,-18)
end
local function effect(name,size,pos,color)
    local p=W.part(world.effects,name,size,pos,color,Enum.Material.Neon)
    p.CanCollide=false; p.CanTouch=false; p.CanQuery=false; hazardObjects[#hazardObjects+1]=p
    return p
end
local nextHazard=0; local moving=nil; local drops={}
local function hazards(elapsed,dt)
    if activeEvent=="sauce" then
        local height=math.min(6,(elapsed-C.PanicAt)*.4)
        world.sauce.Position=Vector3.new(0,height,-18)
        for _,p in ipairs(Players:GetPlayers()) do
            local root=character(p)
            if root and root.Position.Z<33 and root.Position.Y<height+2.5 then bounce(p,"Sauce got your cargo!") end
        end
    elseif activeEvent=="toaster" then
        if not moving and elapsed>=nextHazard then
            local lane=({-61,-32,8,23})[math.random(1,4)]
            local warning=effect("LaneWarning",Vector3.new(116,.1,12),Vector3.new(0,.2,lane),Color3.fromRGB(255,101,85)); warning.Transparency=.3
            local toaster=Creatures.make(C.Creatures[1],world.effects,3,0); toaster:PivotTo(CFrame.new(-70,5,lane))
            hazardObjects[#hazardObjects+1]=toaster
            moving={warning=warning,model=toaster,z=lane,starts=elapsed+2.2}; nextHazard=elapsed+8
        end
        if moving and elapsed>=moving.starts then
            moving.warning.Transparency=.85
            local x=-64+(elapsed-moving.starts)*32
            moving.model:PivotTo(CFrame.new(x,4,moving.z)*CFrame.Angles(0,math.pi/2,0))
            for _,p in ipairs(Players:GetPlayers()) do
                local root=character(p)
                if root and math.abs(root.Position.X-x)<7 and math.abs(root.Position.Z-moving.z)<7 and root.Position.Y<9 then bounce(p,"Toastalotl express!") end
            end
            if x>68 then moving.model:Destroy(); moving.warning:Destroy(); moving=nil end
        end
    else
        if elapsed>=nextHazard then
            nextHazard=elapsed+1.8
            local slot=world.slots[math.random(1,#world.slots)]; local pos=slot.position
            local marker=effect("PopcornWarning",Vector3.new(.12,17,17),Vector3.new(pos.X,.17,pos.Z),Color3.fromRGB(255,220,95))
            marker.Shape=Enum.PartType.Cylinder; marker.Orientation=Vector3.new(0,0,90); marker.Transparency=.3
            local corn=effect("Popcorn",Vector3.new(5,5,5),Vector3.new(pos.X,42,pos.Z),Color3.fromRGB(255,242,180)); corn.Shape=Enum.PartType.Ball
            drops[#drops+1]={marker=marker,corn=corn,pos=pos,starts=elapsed+2,hit=false}
        end
        for i=#drops,1,-1 do
            local d=drops[i]; local age=elapsed-d.starts
            if age>=0 then
                d.corn.Position=Vector3.new(d.pos.X,math.max(2,42-age*85),d.pos.Z)
                if age>=.46 and not d.hit then
                    d.hit=true
                    for _,p in ipairs(Players:GetPlayers()) do
                        local root=character(p)
                        if root and root.Position.Z<33 and (Vector3.new(root.Position.X,0,root.Position.Z)-Vector3.new(d.pos.X,0,d.pos.Z)).Magnitude<8.5 then bounce(p,"Popcorn landing!") end
                    end
                end
                if age>1 then d.corn:Destroy(); d.marker:Destroy(); table.remove(drops,i) end
            end
        end
    end
end
setPhase("IDLE",0)
task.spawn(function()
    while not closing do
        while #Players:GetPlayers()==0 and not closing do task.wait(1) end
        if closing then break end
        round=round+1; teamCharge=0; frenzyUntil=0; goal=math.max(4,#Players:GetPlayers()*2)
        activeEvent=R.voteWinner(votes,ids,ids[((round-1)%#ids)+1]); votes={}
        for _,rt in pairs(runtime) do rt.deliveries=0; rt.bounces=0 end
        resetHazards(); clearTokens(); moving=nil; drops={}; nextHazard=C.PanicAt
        local started=now(); local endsAt=started+C.RoundSeconds
        setPhase("HUNT",endsAt)
        for _,slot in ipairs(world.slots) do spawnToken(slot,round) end
        announce("ROUND "..round..": rescue creatures before the snackquake!","good")
        while now()<endsAt and not closing do
            local elapsed=now()-started
            if elapsed>=C.PanicAt and phase~="PANIC" then setPhase("PANIC",endsAt); announce(state:GetAttribute("Hint"),"danger")
            elseif elapsed>=C.WarningAt and elapsed<C.PanicAt and phase~="WARNING" then
                setPhase("WARNING",endsAt); announce(state:GetAttribute("EventName").." in 7 seconds. Find your escape route!","danger")
            end
            if phase=="PANIC" then hazards(elapsed,.1) end
            for _,p in ipairs(Players:GetPlayers()) do
                local root=character(p)
                if root and (root.Position.Y< -8 or math.abs(root.Position.X)>65 or root.Position.Z< -80 or root.Position.Z>78) then bounce(p,"Back to safety!") end
            end
            task.wait(.1)
        end
        if closing then break end
        clearTokens(); resetHazards(); setPhase("BREAK",now()+C.BreakSeconds); frenzyUntil=0; state:SetAttribute("FrenzyUntil",0)
        local topCount=0; local topName="Nobody yet"
        for _,p in ipairs(Players:GetPlayers()) do
            local rt=runtime[p]; local rec=Data.get(p)
            if rt and rec then
                local bonus,won=R.roundBonus(rt.deliveries,rt.bounces)
                bonus=math.min(bonus,C.MaxFizz-rec.profile.fizz)
                rec.profile.fizz=rec.profile.fizz+bonus
                if won then rec.profile.wins=math.min(C.MaxFizz,rec.profile.wins+1) end
                rec.profile.best=math.max(rec.profile.best,rt.deliveries)
                if bonus>0 then
                    Data.changed(p); Analytics.economy(p,bonus,rec.profile.fizz,"RoundBonus")
                    Analytics.custom(p,"RoundRescues",rt.deliveries)
                    if not rt.firstRound then rt.firstRound=true; Analytics.step(p,4,"FirstRoundCompleted") end
                end
                if rt.deliveries>topCount then topCount=rt.deliveries; topName=p.DisplayName end
                drop(p); sync(p)
                Remote:FireClient(p,{kind="result",rescues=rt.deliveries,bounces=rt.bounces,bonus=bonus,clean=won})
            end
        end
        -- Player names stay in the built-in player list; generated world text remains fixed.
        world.board.Text="BRAINROT RESCUE\nROUND "..round.." BEST: "..topCount.." RESCUES\nVote for the next disaster!"
        local untilTime=now()+C.BreakSeconds
        while now()<untilTime and not closing do task.wait(.2) end
        if #Players:GetPlayers()==0 then setPhase("IDLE",0) end
    end
end)
