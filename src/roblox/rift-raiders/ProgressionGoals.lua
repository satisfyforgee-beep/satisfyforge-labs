-- v0.16: onboarding + repeatable earned-coin daily challenges.
-- One server-owned progression state per player. No Robux, real-world cash,
-- hidden monetization, data collection or client-provided rewards.
local Goals={}
local config={
 {kind="Travel",arg="SUBURBIA",name="STEP INTO THE WORLD",
  text="Explore the detailed suburb! Tap GO TO SUBURBIA below.",reward=40,xp=8},
 {kind="Buy",arg="",name="MAKE YOUR FIRST PURCHASE",
  text="Open LIFE SHOPPING at the Suburban Market and buy any affordable item.",reward=85,xp=12},
 {kind="Career",arg="",name="CHOOSE YOUR FIRST CAREER",
  text="Visit the Suburban Retail, Courier, Security or Mechanic workstation and APPLY.",reward=45,xp=15},
 {kind="SHIFT",arg="",name="EARN YOUR FIRST PAYCHECK",
  text="Start a work shift, finish both tasks, then collect wages.",reward=155,xp=22},
}
local daily={
 {kind="SHIFT",required=1,title="Finish one honest day's work",reward=105,xp=15},
 {kind="BuySnack",required=1,title="Enjoy a meal at the market",reward=65,xp=10},
 {kind="Travel",arg="SUBURBIA",required=1,title="Return to the suburb",reward=55,xp=8},
 {kind="GardenHarvest",required=1,title="Harvest your garden",reward=90,xp=14},
}
Goals.Intro=config;Goals.Daily=daily
local callbacks
local function clampInt(value,limit)
 return math.clamp(math.floor(tonumber(value) or 0),0,limit)
end
function Goals.DayKey(epoch)
 local t=os.date("!*t",epoch or os.time())
 return t.year*10000+t.month*100+t.day
end
function Goals.Normalize(raw)
 raw=type(raw)=="table" and raw or {}
 local day=clampInt(raw.day,99999999)
 local today=Goals.DayKey()
 local record={intro=clampInt(raw.intro,#config),
  day=today,completed=0,counters={}}
 if day==today and type(raw.counters)=="table" then
  for i,entry in ipairs(daily) do
   record.counters[i]=clampInt(raw.counters[i],entry.required)
  end
 end
 for i,entry in ipairs(daily) do
  record.counters[i]=record.counters[i] or 0
 end
 if day==today then
  for i,entry in ipairs(daily) do
   if record.counters[i]>=entry.required then record.completed+=1 end
  end
 end
 return record
end
function Goals.Initialize(options)
 callbacks=options
end
function Goals.RefreshDay(s)
 if not s then return end
 local today=Goals.DayKey()
 if s.day~=today then
  s.day=today;s.completed=0
  s.counters={}
  for i in ipairs(daily) do s.counters[i]=0 end
 end
end
function Goals.Sync(player)
 if not callbacks then return end
 local profile=callbacks.getProfile(player)
 if not profile then return end
 local g=profile.goals
 if not g then return end
 Goals.RefreshDay(g)
 local step=math.clamp(g.intro+1,1,#config)
 local instruction=config[step]
 player:SetAttribute("RRGoalsIntro",g.intro)
 player:SetAttribute("RRGoalsIntroCount",#config)
 player:SetAttribute("RRGoalsIntroTitle",
  g.intro>=#config and "YOU ARE A RIFTLIFE CITIZEN!" or instruction.name)
 player:SetAttribute("RRGoalsIntroHint",
  g.intro>=#config and "Explore, work, garden, drive and meet friends." or instruction.text)
 player:SetAttribute("RRGoalsIntroDone",g.intro>=#config)
 player:SetAttribute("RRGoalsToday",g.day)
 player:SetAttribute("RRGoalsDailyDone",g.completed)
 player:SetAttribute("RRGoalsDailyTotal",#daily)
 for i,entry in ipairs(daily) do
  player:SetAttribute("RRGoalsDaily_"..i,
   math.min(entry.required,g.counters[i] or 0))
 end
end
function Goals.Record(player,kind,arg)
 if not callbacks or type(kind)~="string" then return false end
 local p=callbacks.getProfile(player)
 if not p or not p.goals then return false end
 local g=p.goals
 Goals.RefreshDay(g)
 local introReward=false
 local current=config[g.intro+1]
 if current and current.kind==kind and
  (current.arg=="" or current.arg==arg) then
  g.intro+=1
  callbacks.reward(player,current.reward,current.xp,0)
  callbacks.tell(player,"RIFTLIFE FIRST STEPS • "..current.name..
   " COMPLETE! +"..current.reward.." COINS. "..g.intro..
   "/"..#config.." STEPS")
  introReward=true
 end
 local dailyReward=false
 for i,entry in ipairs(daily) do
  if entry.kind==kind and (not entry.arg or entry.arg==arg) then
   local old=g.counters[i] or 0
   if old<entry.required then
    g.counters[i]=math.min(entry.required,old+1)
    if g.counters[i]==entry.required then
     g.completed+=1
     callbacks.reward(player,entry.reward,entry.xp,0)
     callbacks.tell(player,"DAILY COMPLETE: "..entry.title:upper()..
      "! +"..entry.reward.." COINS.")
     dailyReward=true
    end
   end
  end
 end
 Goals.Sync(player)
 return introReward or dailyReward
end
return Goals
