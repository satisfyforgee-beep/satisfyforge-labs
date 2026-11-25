-- Earned prestige catalog. Every item is earned with in-game coins.
-- NO Robux product IDs or purchase prompts are configured in this prototype.
local Catalog={}
Catalog.Items={
 {id="CITY_WRAP",name="Midnight City Car Wrap",category="vehicle",
  level=3,coins=450,description="Deep midnight paint for your personal car"},
 {id="ESTATE_ROOF",name="Modern Estate Roof",category="home",
  level=5,coins=1200,description="Slate roof and warm exterior lighting"},
 {id="PLATINUM_WRAP",name="Platinum Hypercar Finish",category="vehicle",
  level=10,coins=3800,description="Reflective platinum finish for personal vehicles"},
 {id="HOME_GARAGE",name="Luxury Home Garage",category="home",
  level=12,coins=6000,wood=10,metal=8,
  description="Build a full garage and private driveway at your house"},
 {id="SNOWMOBILE_LICENSE",name="Snowmobile Driver License",category="vehicle",
  level=5,coins=1400,description="Earn permanent access to ride snowmobiles"},
 {id="JETPACK_LICENSE",name="Jetpack Pilot License",category="vehicle",
  level=7,coins=2200,description="Unlock jetpack launches at the Arctic station"},
 {id="FLIGHT_LICENSE",name="Flying Car Pilot License",category="vehicle",
  level=12,coins=6500,description="Unlock flying cars for advanced exploration"},
 {id="AURORA_TRAIL",name="Aurora Legend Trail",category="avatar",
  level=18,coins=9000,description="An animated glowing trail following your character"},
}
Catalog.ById={}
for _,entry in ipairs(Catalog.Items) do Catalog.ById[entry.id]=entry end
function Catalog.ValidateOwned(value)
 local clean={}
 if type(value)=="table" then
  for _,entry in ipairs(Catalog.Items) do
   if value[entry.id]==true then clean[entry.id]=true end
  end
 end
 return clean
end
function Catalog.PriceText(entry)
 local extra=(entry.wood and (" + "..entry.wood.." wood + "..entry.metal.." metal")) or ""
 return entry.coins.." coins"..extra.." | level "..entry.level
end
return Catalog
