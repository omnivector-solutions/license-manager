# License Manager Prolog/Epilog API

A simple FastAPI service that exposes endpoints for Slurm prolog and epilog hooks to communicate job lifecycle events for license management.

## Endpoints

- `POST /prolog` - Called when a job starts (prolog hook)
- `POST /epilog` - Called when a job ends (epilog hook)

## Request Body

Both endpoints accept the same request body:

```json
{
    "cluster_name": "string",
    "job_id": "string",
    "lead_host": "string",
    "user_name": "string",
    "job_licenses": "string"
}
```

## Running

```bash
uvicorn lm_prolog_epilog_api.main:app --host 0.0.0.0 --port 8000
```
