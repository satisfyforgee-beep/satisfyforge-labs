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
 {id="PARAMEDIC",name="Paramedic",wage=46,level=5},
 {id="FIREFIGHTER",name="Firefighter",wage=48,level=5},
 {id="CHEF",name="Restaurant Chef",wage=32,level=2},
 {id="FARMER",name="Farmer",wage=29,level=1},
 {id="TEACHER",name="Teacher",wage=43,level=5},
 {id="SANITATION",name="Sanitation Worker",wage=27,level=1},
 {id="ELECTRICIAN",name="Electrician",wage=42,level=4},
 {id="PLUMBER",name="Plumber",wage=39,level=3},
 {id="VETERINARIAN",name="Veterinarian",wage=45,level=6},
 {id="REAL_ESTATE_AGENT",name="Real Estate Agent",wage=50,level=7},
 {id="PHOTOGRAPHER",name="Photographer",wage=30,level=2},
 {id="PILOT",name="Airline Pilot",wage=62,level=10},
 {id="MUSICIAN",name="Musician",wage=33,level=3},
}
Catalog.CareerById={}
for _,career in ipairs(Catalog.Careers) do Catalog.CareerById[career.id]=career end
Catalog.Items={
 {id="PHONE",name="Basic Smartphone",category="TECH",price=90,level=1},
 {id="HOODIE",name="Streetwear Hoodie",category="APPAREL",price=120,level=1},
 {id="SNEAKERS",name="Running Sneakers",category="APPAREL",price=160,level=1},
 {id="GROCERIES",name="Kitchen Groceries",category="HOME",price=35,level=1},
 {id="WORK_BOOTS",name="Work Boots",category="APPAREL",price=180,level=1},
 {id="SUIT",name="Business Suit",category="APPAREL",price=700,level=4},
 {id="FURNITURE",name="Furniture Starter Set",category="HOME",price=550,level=2},
 {id="GUITAR",name="Acoustic Guitar",category="TECH",price=390,level=2},
 {id="FIRST_AID_KIT",name="First Aid Kit",category="HOME",price=130,level=1},
 {id="WRENCH_SET",name="Mechanic Tool Set",category="HOME",price=180,level=1},
 {id="SMART_TV",name="Smart Television",category="TECH",price=730,level=3},
 {id="CAMERA",name="Creator Camera",category="TECH",price=450,level=2},
 {id="MIC",name="Studio Microphone",category="TECH",price=260,level=2},
 {id="WORKSTATION",name="Editing Workstation",category="TECH",price=850,level=4},
 {id="DESIGNER_OUTFIT",name="Designer Outfit",category="APPAREL",price=900,level=5},
 {id="LAPTOP",name="Professional Laptop",category="TECH",price=1250,level=5},
 {id="TABLET",name="Tablet Computer",category="TECH",price=540,level=2},
 {id="HEADPHONES",name="Wireless Headphones",category="TECH",price=220,level=1},
 {id="GAME_CONSOLE",name="Game Console",category="TECH",price=650,level=3},
 {id="DESKTOP_PC",name="Desktop Computer",category="TECH",price=1100,level=4},
 {id="JEANS",name="Everyday Jeans",category="APPAREL",price=220,level=1},
 {id="WINTER_JACKET",name="Winter Jacket",category="APPAREL",price=320,level=2},
 {id="WATCH",name="Wrist Watch",category="APPAREL",price=450,level=3},
 {id="FORMAL_SHOES",name="Formal Shoes",category="APPAREL",price=380,level=3},
 {id="COUCH",name="Living Room Couch",category="HOME",price=500,level=2},
 {id="BED_SET",name="Bedroom Set",category="HOME",price=650,level=2},
 {id="KITCHEN_APPLIANCES",name="Kitchen Appliance Set",category="HOME",price=800,level=3},
 {id="TOOL_CHEST",name="Workshop Tool Chest",category="HOME",price=450,level=2},
 {id="LAWN_MOWER",name="Lawn Mower",category="HOME",price=700,level=3},
 {id="BIKE",name="Commuter Bicycle",category="VEHICLE",price=600,level=2},
 {id="SEDAN",name="Family Sedan",category="VEHICLE",price=2400,level=6},
 {id="SPORTS_CAR",name="Sports Coupe",category="VEHICLE",price=12500,level=15},
 {id="FISHING_BOAT",name="Fishing Boat",category="VEHICLE",price=3900,level=8},
 {id="YACHT",name="Luxury Yacht",category="VEHICLE",price=35000,level=24},
 {id="APARTMENT",name="Downtown Apartment",category="PROPERTY",price=3500,level=7},
 {id="TOWNHOUSE",name="Family Townhouse",category="PROPERTY",price=9000,level=12},
 {id="MANSION",name="Luxury Mansion",category="PROPERTY",price=65000,level=30},
 {id="CONDO",name="Downtown Condo",category="PROPERTY",price=14000,level=15},
 {id="COMMERCIAL_UNIT",name="Commercial Storefront",category="PROPERTY",price=22000,level=18},
 {id="CAFE_BUSINESS",name="Own a Cafe",category="BUSINESS",price=5000,level=9},
 {id="AUTO_BUSINESS",name="Own an Auto Shop",category="BUSINESS",price=12000,level=15},
 {id="MEDIA_BUSINESS",name="Own a Media Studio",category="BUSINESS",price=18000,level=18},
 {id="REALTY_BUSINESS",name="Own a Realty Office",category="BUSINESS",price=25000,level=22},
 {id="CLOTHING_BUSINESS",name="Own a Clothing Store",category="BUSINESS",price=8000,level=12},
 {id="RESTAURANT_BUSINESS",name="Own a Restaurant",category="BUSINESS",price=15000,level=16},
 {id="DELIVERY_BUSINESS",name="Own a Delivery Company",category="BUSINESS",price=16000,level=16},
 {id="TECH_BUSINESS",name="Own a Technology Store",category="BUSINESS",price=24000,level=20},
 {id="CONSTRUCTION_BUSINESS",name="Own a Construction Company",category="BUSINESS",price=30000,level=22},
}
Catalog.ById={}
for _,entry in ipairs(Catalog.Items) do Catalog.ById[entry.id]=entry end
Catalog.ShopLocations={
 TECH="Creator Technology Store",APPAREL="Clothing Boutique",
 HOME="Home Supply Store",VEHICLE="Vehicle and Marine Dealer",
 PROPERTY="Real Estate Agency",BUSINESS="Business Licensing Office",
}
Catalog.BusinessPayouts={CAFE_BUSINESS=90,AUTO_BUSINESS=190,
 MEDIA_BUSINESS=270,REALTY_BUSINESS=360,CLOTHING_BUSINESS=130,
 RESTAURANT_BUSINESS=230,DELIVERY_BUSINESS=210,TECH_BUSINESS=310,
 CONSTRUCTION_BUSINESS=390}
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
