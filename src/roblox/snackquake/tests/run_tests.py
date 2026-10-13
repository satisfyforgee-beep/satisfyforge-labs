"""Parse Lua-compatible Luau sources and execute pure-rule/persistence tests.
This is not a Roblox engine or Studio compatibility test.
"""
from pathlib import Path
import ctypes as ct
import ctypes.util
import json
import os

root=Path(__file__).resolve().parents[1]
lib = os.environ.get('LUA54_LIBRARY') or ctypes.util.find_library('lua5.4')
if not lib:
    fallback = Path.home() / 'SatisfyForge/tools/lua54/liblua5.4.dylib'
    if fallback.is_file():
        lib = str(fallback)
if not lib:
    raise RuntimeError('Lua 5.4 library not found; set LUA54_LIBRARY or install Lua 5.4')
lua=ct.CDLL(lib)
lua.luaL_newstate.restype=ct.c_void_p
lua.luaL_openlibs.argtypes=[ct.c_void_p]
lua.luaL_loadfilex.argtypes=[ct.c_void_p,ct.c_char_p,ct.c_char_p]
lua.luaL_loadstring.argtypes=[ct.c_void_p,ct.c_char_p]
lua.lua_pcallk.argtypes=[ct.c_void_p,ct.c_int,ct.c_int,ct.c_int,ct.c_longlong,ct.c_void_p]
lua.lua_tolstring.argtypes=[ct.c_void_p,ct.c_int,ct.POINTER(ct.c_size_t)]
lua.lua_tolstring.restype=ct.c_char_p
lua.lua_close.argtypes=[ct.c_void_p]

def run(path,execute=False):
    state=lua.luaL_newstate()
    try:
        lua.luaL_openlibs(state)
        setup=('arg={'+json.dumps(str(root/'src'))+'}').encode()
        if lua.luaL_loadstring(state,setup) or lua.lua_pcallk(state,0,0,0,0,None):
            raise RuntimeError('test setup failed')
        code=lua.luaL_loadfilex(state,str(path).encode(),None)
        if not code and execute: code=lua.lua_pcallk(state,0,0,0,0,None)
        if code: raise AssertionError(f'{path.name}: '+lua.lua_tolstring(state,-1,None).decode())
    finally: lua.lua_close(state)

files=sorted((root/'src').glob('*.lua'))
for f in files: run(f)
print(f'syntax: {len(files)} Lua-compatible Luau files parsed',flush=True)
for f in sorted((root/'tests').glob('*_test.lua')): run(f,True)
print('PASS. Roblox Studio runtime and device playtests remain required.',flush=True)
