-- Session-locked Roblox player data access; v0.18.
-- All UpdateAsync transforms are pure and non-yielding. Existing player
-- records are copied rather than discarded, preserving unknown future keys.
local Persistence={}
Persistence.TTL=300
Persistence.Attempts=3
local function copy(t)
 local out={}
 if type(t)=="table" then
  for k,v in pairs(t) do out[k]=v end
 end
 return out
end
function Persistence.IsLocked(record,token,now)
 if type(record)~="table" then return false end
 local session=record._session
 return type(session)=="table" and
  type(session.id)=="string" and session.id~="" and
  session.id~=token and
  type(session.expiresAt)=="number" and session.expiresAt>now
end
function Persistence.CanAcquire(record,token,now,version)
 if Persistence.IsLocked(record,token,now) then return false end
 return type(record)~="table" or
  type(record.version)~="number" or record.version<=version
end
local function attempt(op)
 local lastError=""
 for n=1,Persistence.Attempts do
  local ok,result=pcall(op)
  if ok then return true,result end
  lastError=tostring(result)
  if n<Persistence.Attempts then
   task.wait(.4*(2^(n-1))+math.random()*.15)
  end
 end
 return false,lastError
end
function Persistence.Acquire(store,key,token,version)
 if not store or type(token)~="string" or token=="" then
  return false,"INVALID_SESSION"
 end
 local now=os.time()
 local ok,result=attempt(function()
  return store:UpdateAsync(key,function(previous,keyInfo)
   if not Persistence.CanAcquire(previous,token,now,version) then
    return nil
   end
   local data=copy(previous)
   data._session={id=token,expiresAt=now+Persistence.TTL}
   if keyInfo then
    return data,keyInfo:GetUserIds(),keyInfo:GetMetadata()
   end
   return data
  end)
 end)
 if not ok then return false,"DATASTORE_ERROR: "..tostring(result) end
 if type(result)~="table" or
  type(result._session)~="table" or result._session.id~=token then
  return false,"PROFILE_IN_USE_OR_NEWER_VERSION"
 end
 return true,result
end
function Persistence.Release(store,key,token)
 -- Player may disconnect after UpdateAsync acquired their profile but
 -- before the profile exists in this server's active player table.
 local ok,result=attempt(function()
  return store:UpdateAsync(key,function(previous,keyInfo)
   if type(previous)~="table" or
    type(previous._session)~="table" or
    previous._session.id~=token then return nil end
   local value=copy(previous)
   value._session=nil
   if keyInfo then
    return value,keyInfo:GetUserIds(),keyInfo:GetMetadata()
   end
   return value
  end)
 end)
 return ok and type(result)=="table" and result._session==nil
end
function Persistence.Save(store,key,token,payload,release,version)
 if type(payload)~="table" or type(token)~="string" then
  return false,"INVALID_PAYLOAD"
 end
 local now=os.time()
 local ok,result=attempt(function()
  return store:UpdateAsync(key,function(previous,keyInfo)
   if type(previous)~="table" or
    type(previous._session)~="table" or
    previous._session.id~=token or
    (type(previous.version)=="number" and previous.version>version) then
    return nil
   end
   local value=copy(previous)
   for k,v in pairs(payload) do
    if k~="_session" then value[k]=v end
   end
   if release then
    value._session=nil
   else
    value._session={id=token,expiresAt=now+Persistence.TTL}
   end
   value._lastWrite=now
   if keyInfo then
    return value,keyInfo:GetUserIds(),keyInfo:GetMetadata()
   end
   return value
  end)
 end)
 if not ok then return false,"DATASTORE_ERROR: "..tostring(result) end
 if type(result)~="table" or
  type(result.version)~="number" or result.version~=version or
  (not release and (type(result._session)~="table" or
   result._session.id~=token)) or
  (release and result._session~=nil) then
  return false,"SESSION_OWNERSHIP_LOST"
 end
 return true,result
end
return Persistence
