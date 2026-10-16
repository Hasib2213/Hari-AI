# JobBright AI-style A-to-Z Backend

FastAPI + MongoDB + Gemini backend for an independent JobBright-style job discovery,
AI matching, resume tailoring, conversational agent, and staged application workflow.

## Scope

This repository implements the AI/backend foundation for the workflows visible in the
screenshots supplied by the user:

- Natural-language Job Explore
- AI job search intent parsing
- Shared job database search
- Deterministic + Gemini job matching
- Match score and match explanation
- Missing/matching skills
- Company/role Q&A
- Candidate profile context
- Resume analysis
- Resume improvement suggestions
- Job-specific custom resume generation
- Custom resume approval/tweak state
- Cover-letter generation and rewriting
- ATS/keyword analysis
- Screening-question assistance
- Agent conversation memory
- Application queue
- Application run state machine
- Application-site analysis
- Semantic application-field mapping
- Browser autofill through Playwright
- Required-field readiness checks
- Explicit submission gate
- Application confirmation/audit record

### Important source boundary

The screenshots show UI and workflow behavior, not JobBright's private source code,
prompts, exact matching formula, proprietary data feeds, or internal agent architecture.
This repository is therefore an independent implementation of the **observable
functionality**, not a copy of JobBright's proprietary implementation.

## Architecture

```text
                         React / Next.js
                               |
                         FastAPI REST API
                               |
                 +-------------+-------------+
                 |                           |
             Agent Orchestrator          Services
                 |                           |
        +--------+--------+        +---------+---------+
        |        |        |        |                   |
     Explore  Match    Resume   Cover/ATS        Applications
        |        |        |        |                   |
        +--------+--------+--------+-------------------+
                               |
                            Gemini
                               |
                           MongoDB
                               |
                         Playwright
                               |
                    External application site
```

## AI agents

### 1. Explore Agent

Natural-language commands such as:

- "Give me more frontend jobs in Canada"
- "Find senior React jobs"
- "I want to adjust my job matches"

The agent converts text into a structured intent/search request. It does not directly
perform browser actions.

### 2. Matching Agent

Input:

```text
Candidate profile + resume
+
Job title + description + skills + location + level
```

Output:

```text
score
reasons
matching skills
missing skills
```

A deterministic baseline is calculated first. Gemini supplies semantic reasoning.
The score returned by this implementation is **not JobBright's proprietary score**.

### 3. Career / Research Agent

Answers company/role questions using supplied context. In production, connect this
agent to a compliant web/company-data provider or your central job/company database.
Do not let an LLM invent current company facts.

### 4. Resume Agent

Supports:

- Resume parsing/normalization
- Resume quality analysis
- Improvement suggestions
- Job-specific resume
- ATS keyword optimization
- Approval/tweak workflow

### 5. Cover Letter Agent

Generates a job-specific cover letter and can rewrite it for:

- tone
- opening
- conciseness
- stronger job alignment

### 6. Application Agent

Orchestrates:

```text
queued
  -> generating_resume
  -> awaiting_resume_approval
  -> analyzing_site
  -> filling_form
  -> awaiting_submission_confirmation
  -> submitted
  -> completed
```

### 7. Form Mapping Agent

Takes browser-extracted fields and candidate data and returns a structured mapping.
It should never invent a personal/legal answer.

### 8. Browser Automation Agent

Playwright performs deterministic actions:

- navigate
- inspect DOM
- fill supported controls
- upload files
- capture screenshot
- detect missing required fields

It is separate from Gemini.

## A-to-Z feature map

### A — Agent conversation
`POST /api/agent/chat/{user_id}`

### B — Browser application
`POST /api/applications/{user_id}/{run_id}/analyze`

### C — Custom resume
`POST /api/resumes/{user_id}/custom/{job_id}`

### D — Discovery
`POST /api/jobs/explore/{user_id}`

### E — Explanation
Match reasons and missing skills are returned.

### F — Form mapping
`POST /api/applications/{user_id}/{run_id}/map-fields`

### G — Gemini
Centralized in `app/services/gemini.py`.

### H — Human approval
Resume approval and final submission are explicit states.

### I — Intent
Structured Gemini intent router.

### J — Job database
MongoDB `jobs` collection.

### K — Keyword/ATS analysis
`POST /api/resumes/{user_id}/ats/{job_id}`

### L — Language generation
Resume/cover letter/chat.

### M — Matching
`POST /api/matching/{user_id}/job/{job_id}`

### N — Natural-language search
Handled by Explore Agent.

### O — Orchestration
`ApplicationAgent`.

### P — Profile
Candidate master profile is the source for matching and autofill.

### Q — Questions
Screening-question analysis and safe answer suggestions.

### R — Resume analysis
`POST /api/resumes/{user_id}/analyze`

### S — Submission gate
Actual external submission is disabled by default.

### T — Tracking
Application runs and application records.

### U — User approval
Required before custom-resume progression.

### V — Validation
Pydantic schemas + required field checks.

### W — Workflow
MongoDB-backed application state machine.

### X — External application
Original application URL is retained per job.

### Y — Your job source
Crawler/API adapters can feed the same central jobs collection.

### Z — Zero-duplicate foundation
The repository includes a normalized fingerprint utility. Production crawlers
should calculate it before insert/upsert.

## Job data architecture

The intended client architecture is:

```text
Greenhouse / Lever / Ashby / Workday / company sources / licensed feeds
                              |
                              v
                         Job ingestion
                              |
                              v
                     normalize + fingerprint
                              |
                              v
                        MongoDB jobs
                              |
                              v
                      AI classification
                              |
                              v
                   shared job search/index
                              |
                              v
                     per-user matching
```

Do not crawl separately for each user.

## MongoDB collections

- `users`
- `jobs`
- `resumes`
- `conversations`
- `application_runs`
- `applications`
- `company_context`
- `ai_events`

## Run locally

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium

copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

MongoDB must be running.

Swagger:

```text
http://localhost:8000/docs
```

## Gemini

Set:

```env
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
```

The current Google GenAI Python SDK is used.

## Production safety

The browser layer does not bypass CAPTCHA, MFA, access controls, robots restrictions,
or anti-bot protections. A production system must also comply with each site's terms
and applicable laws.

Sensitive fields such as work authorization, demographic data, and legal attestations
should require explicit user data/confirmation. The AI must not fabricate answers.

## What remains source-specific

A generic browser automation layer cannot guarantee every ATS. Production adapters
should be added for each supported system:

```text
ATSAdapter
├── Greenhouse
├── Lever
├── Ashby
├── Workday
├── SmartRecruiters
└── iCIMS
```

Similarly, production job crawling requires compliant source adapters/feeds. This
repository intentionally does not pretend that an arbitrary website can be scraped
reliably with one generic function.
