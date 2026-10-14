local src=arg[1]
local C=dofile(src.."/Config.lua")
local R=dofile(src.."/Rules.lua")
local tests=0
local function check(value,message) tests=tests+1; assert(value,message) end
local function eq(a,b,message) check(a==b,(message or "equal")..": "..tostring(a).." vs "..tostring(b)) end
local p=R.sanitize({fizz=0/0,speed=999,seen={fake=true},copies={toastalotl=-2},evolution={toastalotl=99},equipped="fake"},C)
eq(p.fizz,0,"NaN balance"); eq(p.speed,3,"upgrade cap"); eq(p.copies.toastalotl,0,"negative copies")
eq(p.evolution.toastalotl,3,"evolution cap"); eq(p.equipped,"","unowned equip"); eq(p.seen.fake,nil,"unknown creature")
for _,bad in ipairs({math.huge,-math.huge,"1",false}) do eq(R.integer(bad,0,10),0,"malformed integer") end
p=R.newProfile()
local reward,first=R.rescue(p,"toastalotl",false,C)
eq(reward,10,"normal rescue"); check(first,"first discovery"); eq(p.equipped,"toastalotl")
R.rescue(p,"toastalotl",false,C); R.rescue(p,"toastalotl",false,C)
local ok,level=R.fuse(p,"toastalotl",C)
check(ok,"three copies fuse"); eq(level,"Neon"); eq(p.copies.toastalotl,0); check(p.seen.toastalotl,"discovery persists after spending copies")
check(not R.fuse(p,"toastalotl",C),"insufficient duplicate fuse rejected")
eq(R.rescue(p,"toastalotl",true,C),17,"evolved frenzy reward")
local before=R.copy(p); check(not R.upgrade(p,C),"insufficient Fizz rejected"); eq(p.fizz,before.fizz)
p.fizz=500
for i=1,3 do check(R.upgrade(p,C),"upgrade "..i) end
eq(p.fizz,90,"exact upgrade costs"); check(not R.upgrade(p,C),"max upgrade rejected")
local balance=p.fizz; eq(R.rescue(p,"hacked",true,C),nil,"unknown ID"); eq(p.fizz,balance,"unknown ID cannot reward")
p.fizz=C.MaxFizz-2; eq(R.rescue(p,"cosmocroissant",true,C),2,"balance cap actual reward"); eq(p.fizz,C.MaxFizz)
check(R.canInteract(11,true,true,.25),"near prompt accepted")
check(not R.canInteract(13,true,true,1),"remote pickup denied")
check(not R.canInteract(0/0,true,true,1),"NaN distance denied")
check(not R.canInteract(1,false,true,1),"dead player denied")
check(not R.canInteract(1,true,false,1),"disabled prompt denied")
check(not R.canInteract(1,true,true,.1),"prompt spam denied")
check(not R.canDeliver(.5,100),"impossible transit denied"); check(R.canDeliver(2,100),"reasonable transit allowed")
check(not R.canDeliver(0/0,100),"NaN transit denied")
eq(R.roundBonus(0,0),0,"AFK gets no bonus")
local bonus,win=R.roundBonus(3,0); eq(bonus,30); check(win,"clean round win")
bonus,win=R.roundBonus(3,1); eq(bonus,15); check(not win,"bounced round")
eq(R.voteWinner({[1]="toaster",[2]="toaster",[3]="fake"},{"sauce","toaster","popcorn"},"sauce"),"toaster")
eq(R.voteWinner({}, {"sauce","toaster","popcorn"},"popcorn"),"popcorn","tie rotation")
math.randomseed(72319)
for i=1,3000 do
    p=R.sanitize({fizz=math.random(-1000,C.MaxFizz+1000),speed=math.random(-4,9),copies={toastalotl=math.random(-4,10010)},evolution={toastalotl=math.random(-4,9)}},C)
    local old=p.fizz; local amount=R.rescue(p,C.Creatures[math.random(1,#C.Creatures)].id,i%2==0,C)
    check(p.fizz>=0 and p.fizz<=C.MaxFizz and p.fizz==old+amount,"rescue conservation")
    local snapshot=R.copy(p); local purchased,cost=R.upgrade(p,C)
    if purchased then eq(p.fizz,snapshot.fizz-cost,"purchase conservation") else eq(p.fizz,snapshot.fizz,"failed purchase unchanged") end
    check(p.speed>=0 and p.speed<=3,"speed bounded")
end
print("rules: "..tests.." assertions passed")
