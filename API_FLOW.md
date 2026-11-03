# Recommended Frontend Integration Flow

## 1. AI Copilot (Orion Style Multi-Turn Memory)

1. Chat with stateful Copilot:
   `POST /api/agent/chat/{user_id}`
   Body: `{"message": "I want senior frontend roles in Canada with React and TypeScript"}`
   Returns: `assistant_message`, `intent`, `jobs`, and `suggested_followups` (clickable prompt chips).
2. Get conversation history:
   `GET /api/agent/history/{user_id}?limit=30`
3. Clear conversation:
   `DELETE /api/agent/history/{user_id}`

## 2. Resume PDF / Doc Upload & Parsing

1. Upload PDF resume:
   `POST /api/resumes/{user_id}/upload`
   Multipart form: `file` (e.g. `resume.pdf`), query param: `auto_update_profile=true`.
   Auto-populates: `skills`, `target_titles`, `summary`, `years_experience`, `education`, `work_experience`.
2. Parse raw pasted text:
   `POST /api/resumes/parse-text`
   Body: `resume_text`

## 3. Job Ingestion & Smart Match Feed (Jobright.ai /jobs/recommend)

1. Seed realistic sample tech jobs (OpenAI, Google, Amazon, Shopify, Stripe, Meta):
   `POST /api/jobs/seed`
2. Fetch personalized recommended jobs feed:
   `GET /api/matching/{user_id}/recommend?limit=20`
   Returns pre-ranked jobs with match scores (0-100), matching skills, and missing skills.
3. Search with specific query:
   `POST /api/matching/{user_id}/search?query=react+typescript`
4. Detailed single job match breakdown:
   `POST /api/matching/{user_id}/job/{job_id}`

## Custom resume

1. User opens a job.
2. `POST /api/resumes/{user_id}/custom/{job_id}`.
3. Show draft.
4. User approves.
5. Connect the approval to the application-run state.

## Application agent

1. Queue jobs:
   `POST /api/applications/{user_id}/queue/{job_id}`
2. Start:
   `POST /api/applications/{user_id}/start`
3. Generate/attach custom resume.
4. Ask user to approve.
5. Analyze application site:
   `POST /api/applications/{user_id}/{run_id}/analyze`
6. Map fields:
   `POST /api/applications/{user_id}/{run_id}/map-fields`
7. Dry-run fill:
   `POST /api/applications/{user_id}/{run_id}/fill?dry_run=true`
8. User reviews unresolved required fields.
9. Submit only after explicit confirmation and server-side submission enablement.

## Resume tools

- `POST /api/resumes/{user_id}/analyze`
- `POST /api/resumes/{user_id}/ats/{job_id}`
- `POST /api/resumes/{user_id}/cover-letter/{job_id}`
- `POST /api/resumes/{user_id}/cover-letter/rewrite`
- `POST /api/resumes/optimize-section` (Jobright 1-Click "FIX" Button for Experience sections)
  Payload:
  ```json
  {
    "company": "Citibank, N.A.",
    "title": "Senior Java Developer",
    "raw_description": "Worked on core banking and credit-card applications...",
    "bullets": [
      "Worked on core banking microservices with Spring Boot.",
      "Developed secure REST APIs for online banking."
    ],
    "target_role": "Senior Java Developer"
  }
  ```

## AI Mock Interview & Real Company Prep (Jobright.ai Style)

1. Fetch real company questions by company, role & category:
   `GET /api/interview/questions?company=Google&role=Software Engineer&category=behavioral`
2. View detailed breakdown (Interviewer Intent + Model Answer):
   `GET /api/interview/questions/{question_id}/guide`
3. Practice and submit response for AI STAR evaluation:
   `POST /api/interview/practice/evaluate`
   Payload:
   ```json
   {
     "question_id": "...",
     "question_text": "Tell me about a time you had a technical disagreement with a team member.",
     "company": "Amazon",
     "role": "Software Development Engineer",
     "candidate_answer": "In my last project, we were deciding between PostgreSQL and MongoDB...",
     "user_id": "..."
   }
   ```
4. View past practice history & progress:
   `GET /api/interview/history/{user_id}`
