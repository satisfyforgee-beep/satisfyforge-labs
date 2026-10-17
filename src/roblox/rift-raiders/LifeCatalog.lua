-- All prices are FICTIONAL, in-game coins; no real-world transactions.
local Catalog={}
Catalog.Careers={
 {id="RETAIL",name="Retail Associate",wage=22,level=1},
 {id="COURIER",name="Delivery Driver",wage=28,level=1},
 {id="BARISTA",name="Cafe Barista",wage=25,level=1},
 {id="MECHANIC",name="Auto Mechanic",wage=38,level=3},
 {id="CONSTRUCTION",name="Construction Worker",wage=44,level=4},
 {id="POLICE",name="Police Officer",wage=45,level=5},
 {id="CREATOR",name="Content Creator",wage=0,level=1},
}
Catalog.CareerById={}
for _,career in ipairs(Catalog.Careers) do Catalog.CareerById[career.id]=career end
Catalog.Items={
 {id="PHONE",name="Basic Smartphone",category="TECH",price=90,level=1},
 {id="HOODIE",name="Streetwear Hoodie",category="APPAREL",price=120,level=1},
 {id="SNEAKERS",name="Running Sneakers",category="APPAREL",price=160,level=1},
 {id="GROCERIES",name="Kitchen Groceries",category="HOME",price=35,level=1},
 {id="CAMERA",name="Creator Camera",category="TECH",price=450,level=2},
 {id="MIC",name="Studio Microphone",category="TECH",price=260,level=2},
 {id="WORKSTATION",name="Editing Workstation",category="TECH",price=850,level=4},
 {id="DESIGNER_OUTFIT",name="Designer Outfit",category="APPAREL",price=900,level=5},
 {id="LAPTOP",name="Professional Laptop",category="TECH",price=1250,level=5},
 {id="BIKE",name="Commuter Bicycle",category="VEHICLE",price=600,level=2},
 {id="SEDAN",name="Family Sedan",category="VEHICLE",price=2400,level=6},
 {id="SPORTS_CAR",name="Sports Coupe",category="VEHICLE",price=12500,level=15},
 {id="FISHING_BOAT",name="Fishing Boat",category="VEHICLE",price=3900,level=8},
 {id="YACHT",name="Luxury Yacht",category="VEHICLE",price=35000,level=24},
 {id="APARTMENT",name="Downtown Apartment",category="PROPERTY",price=3500,level=7},
 {id="TOWNHOUSE",name="Family Townhouse",category="PROPERTY",price=9000,level=12},
 {id="MANSION",name="Luxury Mansion",category="PROPERTY",price=65000,level=30},
 {id="CAFE_BUSINESS",name="Own a Cafe",category="BUSINESS",price=5000,level=9},
 {id="AUTO_BUSINESS",name="Own an Auto Shop",category="BUSINESS",price=12000,level=15},
 {id="MEDIA_BUSINESS",name="Own a Media Studio",category="BUSINESS",price=18000,level=18},
 {id="REALTY_BUSINESS",name="Own a Realty Office",category="BUSINESS",price=25000,level=22},
}
Catalog.ById={}
for _,entry in ipairs(Catalog.Items) do Catalog.ById[entry.id]=entry end
Catalog.ShopLocations={
 TECH="Creator Technology Store",APPAREL="Clothing Boutique",
 HOME="Home Supply Store",VEHICLE="Vehicle and Marine Dealer",
 PROPERTY="Real Estate Agency",BUSINESS="Business Licensing Office",
}
Catalog.BusinessPayouts={CAFE_BUSINESS=90,AUTO_BUSINESS=190,
 MEDIA_BUSINESS=270,REALTY_BUSINESS=360}
function Catalog.SanitizeOwned(raw)
 local clean={}
 if type(raw)=="table" then
  for _,entry in ipairs(Catalog.Items) do
   if raw[entry.id]==true then clean[entry.id]=true end
  end
 end
 return clean
end
function Catalog.SanitizeCareer(value)
 return type(value)=="string" and Catalog.CareerById[value] and value or "UNEMPLOYED"
end
return Catalog
