local M={}
local function rgb(v) return Color3.fromRGB(v[1],v[2],v[3]) end
local function part(model,name,size,pos,color,shape)
    local p=Instance.new("Part"); p.Name=name; p.Size=size; p.Position=pos
    p.Anchored=true; p.CanCollide=false; p.CanTouch=false; p.CanQuery=false
    p.Color=color; p.Material=Enum.Material.SmoothPlastic
    p.TopSurface=Enum.SurfaceType.Smooth; p.BottomSurface=Enum.SurfaceType.Smooth
    if shape then p.Shape=shape end
    p.Parent=model; return p
end
function M.make(spec,parent,scale,evolution)
    local model=Instance.new("Model"); model.Name=spec.name
    local color,accent=rgb(spec.color),rgb(spec.accent)
    local body=part(model,"Body",Vector3.new(2.8,2.8,2.2),Vector3.new(0,0,0),color)
    model.PrimaryPart=body
    if spec.kind=="dumpling" or spec.kind=="broccoli" or spec.kind=="croissant" then body.Shape=Enum.PartType.Ball end
    if spec.kind=="fridge" then body.Size=Vector3.new(2.7,4,2.2) end
    for _,side in ipairs({-1,1}) do
        part(model,"Eye",Vector3.new(.67,.85,.25),Vector3.new(side*.65,.45,-1.14),Color3.new(1,1,1),Enum.PartType.Ball)
        part(model,"Pupil",Vector3.new(.28,.4,.2),Vector3.new(side*.68,.41,-1.3),Color3.fromRGB(23,24,41),Enum.PartType.Ball)
        part(model,"Shoe",Vector3.new(1,.45,1.7),Vector3.new(side*.85,-1.55,.12),accent)
    end
    part(model,"Smile",Vector3.new(.7,.18,.2),Vector3.new(0,-.55,-1.22),Color3.fromRGB(33,30,46))
    if spec.kind=="toast" then
        for _,x in ipairs({-.68,.68}) do part(model,"ToastSlot",Vector3.new(.34,.12,1.35),Vector3.new(x,1.45,0),Color3.fromRGB(80,51,30)) end
        for _,s in ipairs({-1,1}) do
            for i=1,3 do local p=part(model,"Gill",Vector3.new(1.1,.3,.35),Vector3.new(s*1.8,(i-2)*.5,0),accent); p.Orientation=Vector3.new(0,0,s*(i-2)*25) end
        end
    elseif spec.kind=="broccoli" then
        for i=1,5 do local a=i*math.pi*2/5; part(model,"Floret",Vector3.new(1.5,1.5,1.5),Vector3.new(math.cos(a)*1.1,1.3,math.sin(a)*.8),color,Enum.PartType.Ball) end
        for _,x in ipairs({-1.2,1.2}) do part(model,"Roller",Vector3.new(.55,.55,.55),Vector3.new(x,-1.7,-.3),Color3.fromRGB(40,40,58),Enum.PartType.Ball) end
    elseif spec.kind=="waffle" then
        for i=-1,1 do
            part(model,"Grid",Vector3.new(.14,2.6,.13),Vector3.new(i*.65,0,1.16),accent)
            part(model,"Grid",Vector3.new(2.6,.14,.13),Vector3.new(0,i*.65,1.16),accent)
        end
        part(model,"ButterHat",Vector3.new(1.4,.6,1.2),Vector3.new(0,1.7,0),Color3.fromRGB(255,250,170))
    elseif spec.kind=="soda" then
        part(model,"Helmet",Vector3.new(3.2,3.2,3),Vector3.new(0,.15,0),Color3.fromRGB(191,240,255),Enum.PartType.Ball).Transparency=.75
        part(model,"Straw",Vector3.new(.3,2,.3),Vector3.new(.6,2,0),accent)
        part(model,"RocketPack",Vector3.new(1.9,2.2,1),Vector3.new(0,.1,1.4),accent)
    elseif spec.kind=="noodle" then
        for i=1,7 do part(model,"Noodle",Vector3.new(.3,2.5,.3),Vector3.new((i-4)*.48,1.5,.3),accent) end
        local ring=part(model,"Orbit",Vector3.new(.25,4.8,4.8),Vector3.new(0,-.25,0),accent,Enum.PartType.Cylinder); ring.Orientation=Vector3.new(0,0,90)
    elseif spec.kind=="fridge" then
        part(model,"DoorLine",Vector3.new(2.5,.12,.15),Vector3.new(0,.7,-1.2),accent)
        part(model,"Handle",Vector3.new(.25,.9,.3),Vector3.new(1,.05,-1.35),accent)
        part(model,"Antenna",Vector3.new(.25,1.2,.25),Vector3.new(0,2.6,0),accent)
    elseif spec.kind=="dumpling" then
        for i=1,5 do part(model,"Pleat",Vector3.new(.25,.9,1),Vector3.new((i-3)*.45,1.2,0),accent) end
        part(model,"DiscoBall",Vector3.new(1,1,1),Vector3.new(0,2.4,0),accent,Enum.PartType.Ball).Material=Enum.Material.Neon
    else
        for _,s in ipairs({-1,1}) do
            part(model,"CrescentTip",Vector3.new(1.5,1.2,1.5),Vector3.new(s*1.7,.65,.2),color,Enum.PartType.Ball)
            part(model,"Star",Vector3.new(.4,.4,.4),Vector3.new(s*2.1,1.9,0),accent).Material=Enum.Material.Neon
        end
    end
    if (evolution or 0)>0 then
        local halo=part(model,"EvolutionHalo",Vector3.new(.1,3.8,3.8),Vector3.new(0,2.5,0),accent,Enum.PartType.Cylinder)
        halo.Orientation=Vector3.new(0,0,90); halo.Material=Enum.Material.Neon
        local light=Instance.new("PointLight"); light.Color=accent; light.Range=9; light.Brightness=.5; light.Parent=body
    end
    model.Parent=parent
    model:ScaleTo(scale or 1)
    return model
end
return M
