-- Pure mobile guidance layout math; shared by the client and Studio QA.
local MobileLayout={}

MobileLayout.LeftInset=12
MobileLayout.RightControlInset=118
MobileLayout.MinimumClearance=15
MobileLayout.DesktopGuideWidth=325
MobileLayout.TouchGuideMaxWidth=265
MobileLayout.TouchGuideMinWidth=160

function MobileLayout.GuideWidth(viewportWidth,touchEnabled)
 local width=tonumber(viewportWidth) or 375
 if not touchEnabled then return MobileLayout.DesktopGuideWidth end
 return math.floor(math.clamp(
  width-MobileLayout.LeftInset-MobileLayout.RightControlInset-
   MobileLayout.MinimumClearance,
  MobileLayout.TouchGuideMinWidth,
  MobileLayout.TouchGuideMaxWidth
 ))
end

function MobileLayout.RightControlClearance(viewportWidth,guideWidth)
 local width=tonumber(viewportWidth) or 375
 local rightStart=width-MobileLayout.RightControlInset
 local leftEnd=MobileLayout.LeftInset+(tonumber(guideWidth) or 0)
 return rightStart-leftEnd
end

return MobileLayout
