local DSS=game:GetService("DataStoreService")
local RunService=game:GetService("RunService")
local HttpService=game:GetService("HttpService")
local Shared=game:GetService("ReplicatedStorage"):WaitForChild("SnackquakeShared")
local C=require(Shared.Config)
local R=require(Shared.Rules)
local P={records={}}
local serverId=game.JobId~="" and game.JobId or HttpService:GenerateGUID(false)
local store
-- Studio is intentionally session-only, even when API access is enabled.
if not RunService:IsStudio() then
    local ok,value=pcall(function() return DSS:GetDataStore(C.DataStoreName) end)
    if ok then store=value else warn("Snackquake: persistence unavailable; session-only mode") end
end
local function try(callback)
    for attempt=1,3 do
        local ok,result=pcall(callback)
        if ok then return true,result end
        if attempt<3 then task.wait(attempt) end
    end
    return false,nil
end
function P.load(player)
    -- A new token per join also protects a fast reconnect into the same server.
    local session=serverId..":"..HttpService:GenerateGUID(false)
    local profile=R.newProfile(); local canSave=false; local status="Session only"
    if store then
        local ok,data=try(function()
            return store:UpdateAsync("u_"..player.UserId,function(old)
                old=type(old)=="table" and old or {}
                local lock=old.session
                if type(lock)=="table" and lock.id~=session and type(lock.untilTime)=="number" and lock.untilTime>os.time() then return nil end
                local clean=R.sanitize(old,C)
                clean.session={id=session,untilTime=os.time()+C.SessionLease}
                return clean
            end)
        end)
        if ok and type(data)=="table" and data.session and data.session.id==session then
            profile=R.sanitize(data,C); canSave=true; status="Cloud save ready"
        else status="Session only - save unavailable" end
    elseif RunService:IsStudio() then status="Studio playtest - session only" end
    local record={profile=profile,canSave=canSave,status=status,saving=false,rev=0,savedRev=0,joined=os.clock(),closing=false,sessionId=session}
    P.records[player]=record
    return record
end
function P.get(player) return P.records[player] end
function P.changed(player)
    local record=P.get(player)
    if record then record.rev=record.rev+1 end
end
function P.save(player,release)
    local record=P.get(player)
    if not record or not record.canSave then return false end
    if record.saving then
        if not release then return false end
        local deadline=os.clock()+12
        repeat task.wait(.1) until not record.saving or os.clock()>deadline
        if record.saving then return false end
    end
    record.saving=true
    local snapshot=R.copy(record.profile); local revision=record.rev
    local ok,written=try(function()
        return store:UpdateAsync("u_"..player.UserId,function(old)
            if type(old)~="table" or type(old.session)~="table" or old.session.id~=record.sessionId then return nil end
            local nextData=R.copy(snapshot)
            if not release then nextData.session={id=record.sessionId,untilTime=os.time()+C.SessionLease} end
            return nextData
        end)
    end)
    record.saving=false
    if ok and written then record.savedRev=revision; record.status="Cloud save ready"; return true end
    if ok and not written then record.canSave=false; record.status="Session only - save ownership changed"
    else record.status="Save delayed - retrying" end
    return false
end
return P
