local C = {}
C.Title = "Brainrot Rescue: Snackquake"
C.Version = "0.2.1-save-fix"
C.RoundSeconds = 105
C.WarningAt = 55
C.PanicAt = 62
C.BreakSeconds = 9
C.MaxTokens = 15
C.RespawnSeconds = 7
C.DataStoreName = "SatisfyForge_Snackquake_v1"
C.SessionLease = 180
C.AutosaveSeconds = 45
C.MaxFizz = 10000000
C.MaxCopies = 9999
C.DailyBaseFizz = 25
C.DailyMaxStreak = 7
C.DailyRescueGoal = 5
C.DailyMissionFizz = 60
-- Replace zero with a real Creator Dashboard game-pass ID after publishing.
-- This is a guaranteed cosmetic only, never a paid random reward.
C.FounderGlowPassId = 0
C.SpeedCosts = {50, 120, 240}
C.EvolutionNames = {"Classic", "Neon", "Cosmic", "Mega"}
C.Events = {
    {id="sauce", name="SAUCE SURGE", hint="The floor is sauce. Climb a blue refuge!"},
    {id="toaster", name="TOASTER STAMPEDE", hint="Red lanes warn you. Step out before the toaster!"},
    {id="popcorn", name="POPCORN METEORS", hint="Move away from the yellow landing circles!"},
}
C.Creatures = {
    {id="toastalotl", name="Toastalotl", kind="toast", rarity="Common", value=10, color={244,182,108}, accent={255,119,169}},
    {id="broccoroller", name="Brocco Roller", kind="broccoli", rarity="Common", value=12, color={80,224,125}, accent={255,126,184}},
    {id="wafflopod", name="Wafflopod", kind="waffle", rarity="Odd", value=18, color={255,197,74}, accent={145,112,255}},
    {id="sodastronaut", name="Sodastronaut", kind="soda", rarity="Odd", value=20, color={85,209,255}, accent={255,238,127}},
    {id="noodlenaut", name="Noodlenaut", kind="noodle", rarity="Wild", value=30, color={255,116,82}, accent={255,223,140}},
    {id="fridgoblin", name="Fridgoblin", kind="fridge", rarity="Wild", value=34, color={178,137,255}, accent={110,255,218}},
    {id="discodumpling", name="Disco Dumpling", kind="dumpling", rarity="Cosmic", value=48, color={245,139,242}, accent={134,255,214}},
    {id="cosmocroissant", name="Cosmo Croissant", kind="croissant", rarity="Cosmic", value=55, color={255,215,129}, accent={143,167,255}},
}
C.ById = {}
for _, creature in ipairs(C.Creatures) do C.ById[creature.id] = creature end
return C
