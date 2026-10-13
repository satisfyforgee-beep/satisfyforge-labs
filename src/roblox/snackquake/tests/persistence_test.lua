local src=arg[1]
local C=dofile(src.."/Config.lua"); local R=dofile(src.."/Rules.lua")
package.preload.config=function() return C end; package.preload.rules=function() return R end
local tests=0
local function check(v,m) tests=tests+1; assert(v,m) end
local database={}; local fail=false; local writes=0; local studio=false
local datastore={}
function datastore:UpdateAsync(key,fn)
    if fail then error("simulated outage") end
    local old=database[key] and R.copy(database[key]) or nil
    local nextData=fn(old)
    if nextData==nil then return nil end
    writes=writes+1; database[key]=R.copy(nextData); return R.copy(nextData)
end
local shared={Config="config",Rules="rules"}
local guid=0
local services={
    DataStoreService={GetDataStore=function() return datastore end},
    RunService={IsStudio=function() return studio end},
    HttpService={GenerateGUID=function() guid=guid+1; return "test-session-"..guid end},
    ReplicatedStorage={WaitForChild=function() return shared end},
}
game={JobId="server-A",GetService=function(_,name) return services[name] end}
task={wait=function() end}; warn=function() end
local D=dofile(src.."/PlayerData.lua"); local player={UserId=100}
local record=D.load(player)
check(record.canSave,"new profile lease acquired")
R.rescue(record.profile,"toastalotl",false,C); D.changed(player)
check(D.save(player,false),"save succeeds"); check(database.u_100.fizz==10,"progress saved")
check(database.u_100.session.id==record.sessionId,"lease retained")
local reconnect={UserId=100}; local fast=D.load(reconnect)
check(not fast.canSave,"fast same-server reconnect cannot claim old lease")
check(not D.save(reconnect,true) and database.u_100.fizz==10,"fast reconnect cannot erase original progress")
local blocked={UserId=101}
database.u_101={fizz=999,session={id="server-B",untilTime=os.time()+100}}
local n=writes; local blockedRecord=D.load(blocked)
check(not blockedRecord.canSave,"active foreign session blocks writes")
check(not D.save(blocked,true),"blocked release cannot write")
check(writes==n and database.u_101.fizz==999,"foreign balance untouched")
local expired={UserId=102}; database.u_102={fizz=777,session={id="server-B",untilTime=os.time()-1}}
local recovered=D.load(expired); check(recovered.canSave and recovered.profile.fizz==777,"expired lease recovered")
fail=true; local offline={UserId=103}; n=writes
local offlineRecord=D.load(offline)
check(not offlineRecord.canSave,"failed load read-only")
R.rescue(offlineRecord.profile,"toastalotl",false,C)
check(not D.save(offline,false) and writes==n,"session-only cannot overwrite real profile")
check(not D.save(player,false),"save outage reported")
check(record.canSave and record.status=="Save delayed - retrying","transient failure retryable")
fail=false; check(D.save(player,false),"save recovery succeeds")
database.u_100.session={id="server-B",untilTime=os.time()+100}; n=writes
record.profile.fizz=900
check(not D.save(player,false),"lost lease rejected")
check(not record.canSave and writes==n and database.u_100.fizz==10,"lost lease cannot overwrite")
check(D.save(expired,true),"final release saved"); check(database.u_102.session==nil,"final release removes lease")
studio=true; local S=dofile(src.."/PlayerData.lua"); n=writes
local sp={UserId=104}; local sr=S.load(sp)
check(not sr.canSave and not S.save(sp,true) and writes==n,"Studio never writes production data")
print("persistence: "..tests.." assertions passed")
