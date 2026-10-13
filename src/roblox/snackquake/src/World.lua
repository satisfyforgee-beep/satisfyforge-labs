local W={}
local Lighting=game:GetService("Lighting")
function W.part(parent,name,size,pos,color,material)
    local p=Instance.new("Part"); p.Name=name; p.Anchored=true; p.Size=size; p.Position=pos
    p.Color=color; p.Material=material or Enum.Material.SmoothPlastic
    p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth; p.Parent=parent
    return p
end
function W.label(part,text,color,width,height)
    local gui=Instance.new("BillboardGui"); gui.Name="Label"; gui.Size=UDim2.fromOffset(width or 230,height or 60)
    gui.StudsOffset=Vector3.new(0,3.6,0); gui.AlwaysOnTop=false; gui.MaxDistance=140; gui.Parent=part
    local label=Instance.new("TextLabel"); label.Size=UDim2.fromScale(1,1); label.BackgroundTransparency=.2
    label.BackgroundColor3=Color3.fromRGB(18,21,39); label.TextColor3=color or Color3.new(1,1,1)
    label.Text=text; label.TextSize=16; label.Font=Enum.Font.GothamBold; label.TextWrapped=true; label.Parent=gui
    local corner=Instance.new("UICorner"); corner.CornerRadius=UDim.new(0,10); corner.Parent=label
    return label
end
function W.prompt(part,action,object)
    local p=Instance.new("ProximityPrompt"); p.ActionText=action; p.ObjectText=object
    p.MaxActivationDistance=10; p.HoldDuration=.12; p.RequiresLineOfSight=false
    p.KeyboardKeyCode=Enum.KeyCode.E; p.GamepadKeyCode=Enum.KeyCode.ButtonX; p.Parent=part
    return p
end
function W.build()
    local preview=workspace:FindFirstChild("SnackquakeEditorPreview")
    if preview then preview:Destroy() end
    local old=workspace:FindFirstChild("SnackquakeWorld")
    if old then old:Destroy() end
    local root=Instance.new("Folder"); root.Name="SnackquakeWorld"; root.Parent=workspace
    local self={root=root,slots={},safeZones={}}
    self.tokens=Instance.new("Folder"); self.tokens.Name="Creatures"; self.tokens.Parent=root
    self.effects=Instance.new("Folder"); self.effects.Name="Disasters"; self.effects.Parent=root
    local dark=Color3.fromRGB(23,29,49); local blue=Color3.fromRGB(76,191,255)
    local lime=Color3.fromRGB(178,255,96); local pink=Color3.fromRGB(255,102,167)
    W.part(root,"Arena",Vector3.new(120,2,115),Vector3.new(0,-1,-16),dark)
    W.part(root,"SafeLobby",Vector3.new(120,2,30),Vector3.new(0,0,55),Color3.fromRGB(48,64,83))
    W.part(root,"LobbyStep",Vector3.new(120,1,10),Vector3.new(0,-.3,36),blue)
    for x=-56,56,8 do W.part(root,"FloorGrid",Vector3.new(.12,.025,109),Vector3.new(x,.02,-16),Color3.fromRGB(47,62,89)) end
    for z=-64,32,8 do W.part(root,"FloorGrid",Vector3.new(115,.025,.12),Vector3.new(0,.02,z),Color3.fromRGB(47,62,89)) end
    for _,x in ipairs({-60,60}) do W.part(root,"SideRail",Vector3.new(2,5,146),Vector3.new(x,1.5,-1),blue) end
    W.part(root,"BackRail",Vector3.new(120,5,2),Vector3.new(0,1.5,-74),pink)
    W.part(root,"LobbyRail",Vector3.new(120,5,2),Vector3.new(0,1.5,71),blue)
    local spawn=Instance.new("SpawnLocation"); spawn.Name="RescueSpawn"; spawn.Size=Vector3.new(10,1,10)
    spawn.Position=Vector3.new(0,1.5,55); spawn.Anchored=true; spawn.Neutral=true; spawn.Duration=0
    spawn.Color=blue; spawn.Material=Enum.Material.Neon; spawn.Parent=root; self.spawn=spawn
    self.bank=W.part(root,"RescueChute",Vector3.new(11,5,7),Vector3.new(0,3.5,43),lime)
    W.label(self.bank,"RESCUE HERE\nBring back one creature",lime,260,65)
    self.bankPrompt=W.prompt(self.bank,"RESCUE + FIZZ","Safe-zone rescue chute")
    local ring=W.part(root,"BankGlow",Vector3.new(18,.1,12),Vector3.new(0,1.1,44),lime,Enum.Material.Neon)
    ring.Transparency=.5; ring.CanCollide=false
    local board=W.part(root,"Scoreboard",Vector3.new(39,15,1),Vector3.new(0,13,70),dark)
    local surface=Instance.new("SurfaceGui"); surface.Face=Enum.NormalId.Front; surface.CanvasSize=Vector2.new(780,300); surface.Parent=board
    self.board=Instance.new("TextLabel"); self.board.Size=UDim2.fromScale(1,1); self.board.BackgroundTransparency=1
    self.board.TextColor3=Color3.new(1,1,1); self.board.Font=Enum.Font.GothamBlack; self.board.TextSize=38
    self.board.Text="BRAINROT RESCUE\nSNACKQUAKE\nGrab. Dodge. Rescue. Evolve."; self.board.Parent=surface
    for i,x in ipairs({-38,38}) do
        local station=W.part(root,"Lab",Vector3.new(15,6,10),Vector3.new(x,4,55),i==1 and pink or blue)
        W.label(station,i==1 and "EVOLUTION LAB\n3 copies = 1 evolution\nOpen COLLECTION" or "SPEED SHOP\nEarn upgrades with Fizz\nOpen UPGRADES",Color3.new(1,1,1),260,90)
    end
    for _,x in ipairs({-36,0,36}) do
        for _,z in ipairs({-48,-15}) do
            local safe=W.part(root,"BlueRefuge",Vector3.new(16,1,12),Vector3.new(x,8,z),blue,Enum.Material.Neon)
            self.safeZones[#self.safeZones+1]=safe
            W.label(safe,"HIGH GROUND",blue,150,28)
            for step=1,4 do W.part(root,"RefugeStair",Vector3.new(12,2*step,4),Vector3.new(x,step,z+18-step*4),Color3.fromRGB(56,95,125)) end
        end
    end
    for row=1,3 do
        for col=1,5 do
            local rows={22,-24,-63}
            local pos=Vector3.new(-48+(col-1)*24,2.7,rows[row])
            self.slots[#self.slots+1]={position=pos,index=#self.slots+1,row=row}
            local base=W.part(root,"RescueSpot",Vector3.new(6,.18,6),Vector3.new(pos.X,.12,pos.Z),row==3 and pink or lime,Enum.Material.Neon)
            base.CanCollide=false
        end
    end
    self.sauce=W.part(self.effects,"Sauce",Vector3.new(116,.25,106),Vector3.new(0,-5,-18),Color3.fromRGB(255,95,59),Enum.Material.Neon)
    self.sauce.CanCollide=false; self.sauce.CanTouch=false; self.sauce.Transparency=.2
    Lighting.ClockTime=17.8; Lighting.Brightness=2; Lighting.Ambient=Color3.fromRGB(115,116,143)
    Lighting.OutdoorAmbient=Color3.fromRGB(127,139,157)
    local bloom=Lighting:FindFirstChild("SnackquakeBloom") or Instance.new("BloomEffect")
    bloom.Name="SnackquakeBloom"; bloom.Intensity=.12; bloom.Size=20; bloom.Threshold=1.6; bloom.Parent=Lighting
    return self
end
return W
