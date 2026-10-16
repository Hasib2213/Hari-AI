import re

def terms(values):
    out=set()
    for v in values:
        out.update(re.findall(r"[a-zA-Z0-9+#.-]+", v.lower()))
    return out

def baseline(profile, job):
    ps=terms(profile.skills); js=terms(job.skills)
    overlap=ps & js
    missing=js - ps
    score=20
    title=job.title.lower()
    if any(t.lower() in title or title in t.lower() for t in profile.target_titles):
        score += 25
    if js:
        score += round(35 * len(overlap)/len(js))
    if profile.remote_only:
        score += 15 if job.remote else -15
    if profile.preferred_locations and any(x.lower() in job.location.lower() for x in profile.preferred_locations):
        score += 5
    if profile.excluded_companies and any(x.lower() == job.company.lower() for x in profile.excluded_companies):
        score = 0
    return max(0,min(100,score)), sorted(overlap), sorted(missing)
