#!/usr/bin/env python3
"""SatisfyForge content factory. Standard library only; no paid APIs.
Generates original draft packs from reusable templates. Does not publish or send email.
Usage: python3 tools/content_factory.py --brand SatisfyForge --topic "missed roofing calls" --audience "roofing contractors" --url https://example.com/audit
"""
import argparse, json, pathlib, re, datetime
TEMPLATES = {
 "short_video": {"hook":"What happens when {audience} ignore {topic}?","scene_1":"Show a realistic example of {topic}.","scene_2":"Demonstrate a practical fix; show only outcomes actually verified.","payoff":"Reveal the before/after difference, clearly labeled as demo unless measured.","cta":"Explore the free audit: {url}"},
 "social_post": {"headline":"One overlooked problem for {audience}: {topic}","body":"Here's a practical way to identify it: review incoming inquiries, flag those without responses, and track the time to follow-up. Use actual records, not made-up success metrics.","cta":"Try the free audit: {url}"},
 "landing_page": {"headline":"Stop losing track of customer inquiries","subheadline":"A simple audit for {audience} to spot follow-up gaps related to {topic}.","cta":"Start your free audit: {url}"},
 "email_draft": {"subject":"Quick idea for improving follow-up","body":"Hi, I noticed {topic} can be a challenge for {audience}. We built a simple audit to help identify missed follow-up opportunities. If useful, here's the link: {url}\n\nBest,\n{brand}"}
}
def slug(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:55] or "campaign"
def main():
 p=argparse.ArgumentParser();p.add_argument("--brand",default="SatisfyForge");p.add_argument("--topic",required=True);p.add_argument("--audience",required=True);p.add_argument("--url",required=True);p.add_argument("--out",default="content/drafts");a=p.parse_args()
 values=vars(a); now=datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
 result={"campaign":a.topic,"audience":a.audience,"generated_utc":now,"status":"draft_requires_review","disclosure":"Do not fabricate testimonials, results, screenshots or client relationships.","assets":{k:{field:text.format(**values) for field,text in item.items()} for k,item in TEMPLATES.items()}}
 path=pathlib.Path(a.out)/f"{now}-{slug(a.topic)}.json";path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8");print(path)
if __name__=="__main__":main()
