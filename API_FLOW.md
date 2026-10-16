# Recommended Frontend Integration Flow

## Explore

1. `POST /api/agent/chat/{user_id}` with natural-language request.
2. `POST /api/matching/{user_id}/search` to obtain ranked jobs.
3. Display match score, reasons, matching skills and missing skills.

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
