-- Pure rules: no Roblox services. Also run by the local test harness.
local R = {}
local function integer(n, lo, hi)
    if type(n) ~= "number" or n ~= n or n == math.huge or n == -math.huge then return lo end
    return math.max(lo, math.min(hi, math.floor(n)))
end
R.integer = integer
function R.newProfile()
    return {version=1, fizz=0, rescues=0, wins=0, best=0, speed=0, equipped="", copies={}, seen={}, evolution={}, lastLoginDay=0, loginStreak=0, missionDay=0, missionRescues=0, missionClaimed=false}
end
function R.sanitize(raw, config)
    local p = R.newProfile()
    if type(raw) ~= "table" then return p end
    for _, k in ipairs({"fizz", "rescues", "wins", "best"}) do p[k] = integer(raw[k], 0, config.MaxFizz) end
    p.speed = integer(raw.speed, 0, #config.SpeedCosts)
    p.lastLoginDay = integer(raw.lastLoginDay, 0, 1000000)
    p.loginStreak = integer(raw.loginStreak, 0, config.DailyMaxStreak)
    p.missionDay = integer(raw.missionDay, 0, 1000000)
    p.missionRescues = integer(raw.missionRescues, 0, config.DailyRescueGoal)
    p.missionClaimed = raw.missionClaimed == true
    for _, c in ipairs(config.Creatures) do
        p.copies[c.id] = integer(type(raw.copies)=="table" and raw.copies[c.id] or 0, 0, config.MaxCopies)
        p.evolution[c.id] = integer(type(raw.evolution)=="table" and raw.evolution[c.id] or 0, 0, 3)
        p.seen[c.id] = (type(raw.seen)=="table" and raw.seen[c.id]==true) or p.copies[c.id]>0 or p.evolution[c.id]>0
    end
    if type(raw.equipped)=="string" and config.ById[raw.equipped] and p.seen[raw.equipped] then p.equipped=raw.equipped end
    return p
end
function R.copy(p)
    local out={}
    for k,v in pairs(p) do
        if type(v)=="table" then out[k]=R.copy(v) else out[k]=v end
    end
    return out
end
function R.rescue(p, id, frenzy, config)
    local spec = config.ById[id]
    if not spec then return nil end
    local reward = math.floor(spec.value * (1 + 0.15 * (p.evolution[id] or 0)) * (frenzy and 1.5 or 1))
    local actual = math.min(reward, config.MaxFizz-p.fizz)
    p.fizz=p.fizz+actual; p.rescues=math.min(config.MaxFizz,p.rescues+1)
    p.copies[id]=math.min(config.MaxCopies,(p.copies[id] or 0)+1)
    local discovered=not p.seen[id]
    p.seen[id]=true
    if p.equipped=="" then p.equipped=id end
    return actual,discovered
end
-- UTC day index is computed by the server, never accepted from a client.
function R.dailyLogin(p, day, config)
    if type(day) ~= "number" or day < 1 or day ~= math.floor(day) then return 0 end
    if p.lastLoginDay == day then return 0 end
    p.loginStreak = (p.lastLoginDay == day-1) and math.min(config.DailyMaxStreak, p.loginStreak+1) or 1
    p.lastLoginDay = day
    local award = math.min(config.MaxFizz-p.fizz, config.DailyBaseFizz*p.loginStreak)
    p.fizz = p.fizz + award
    return award
end
function R.dailyMission(p, day, config)
    if p.missionDay ~= day then
        p.missionDay=day; p.missionRescues=0; p.missionClaimed=false
    end
    if p.missionClaimed then return 0 end
    p.missionRescues=math.min(config.DailyRescueGoal,p.missionRescues+1)
    if p.missionRescues < config.DailyRescueGoal then return 0 end
    p.missionClaimed=true
    local award=math.min(config.MaxFizz-p.fizz,config.DailyMissionFizz)
    p.fizz=p.fizz+award
    return award
end
function R.fuse(p,id,config)
    if not config.ById[id] then return false,"Unknown creature" end
    local level=p.evolution[id] or 0
    if level>=3 then return false,"Already at Mega evolution" end
    if (p.copies[id] or 0)<3 then return false,"Rescue 3 copies to evolve" end
    p.copies[id]=p.copies[id]-3; p.evolution[id]=level+1; p.seen[id]=true; p.equipped=id
    return true,config.EvolutionNames[level+2]
end
function R.upgrade(p,config)
    local cost=config.SpeedCosts[p.speed+1]
    if not cost then return false,"Speed is maxed" end
    if p.fizz<cost then return false,"Need "..(cost-p.fizz).." more Fizz" end
    p.fizz=p.fizz-cost; p.speed=p.speed+1
    return true,cost
end
function R.canInteract(distance,alive,enabled,elapsed)
    return type(distance)=="number" and distance==distance and distance<=12 and distance>=0 and alive and enabled and elapsed>=0.25
end
function R.canDeliver(age,distanceTravelled)
    return type(age)=="number" and age>=math.max(1,distanceTravelled/90)
end
function R.roundBonus(deliveries,bounces)
    if deliveries<1 then return 0,false end
    return math.min(40,5*deliveries)+(bounces==0 and 15 or 0),bounces==0
end
function R.voteWinner(votes,eventIds,fallback)
    local counts={}; local allowed={}
    for _,id in ipairs(eventIds) do allowed[id]=true; counts[id]=0 end
    for _,id in pairs(votes) do if allowed[id] then counts[id]=counts[id]+1 end end
    local winner=fallback; local high=counts[fallback] or 0
    for _,id in ipairs(eventIds) do if counts[id]>high then winner=id; high=counts[id] end end
    return winner,counts
end
return R
