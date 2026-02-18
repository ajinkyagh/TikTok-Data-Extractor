# TikTok Research Data Extractor (Portfolio Project)
**Portfolio project | Research‑grade data pipeline | Safe credential handling**

## Research Context
This extractor supports my ongoing research on social media signals and fairer, more cost‑effective screening approaches. The research is **currently in progress**, and this project represents the **data collection phase** of the work.

**Research paper link (AIS eLibrary):**
```
https://aisel.aisnet.org/neais2024/18/
```

**Presented at:** Global NEAIS Conference — October 23, 2024.

NEAIS presentation deck:
```
https://www.canva.com/design/DAGUQ9WfxbI/Ca4WoqH1ESMvKQ_dsjxNBw/view?utm_content=DAGUQ9WfxbI&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h305d6f954d
```


A focused data collection pipeline using the TikTok Research API. This project emphasizes clean code structure, safe credential handling, and reproducible analysis workflows suitable for a data analyst portfolio.

## What It Does
- Fetches profile, video, and (optional) comment data for a given TikTok username.
- Supports additional endpoints (followers, following, liked, pinned, reposted).
- Logs daily request usage to help stay within API limits.

## Quick Start
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file (copy from `.env.example`) and add your keys:
   ```
   TIKTOK_CLIENT_KEY=...
   TIKTOK_CLIENT_SECRET=...
   ```
4. Open `Tiktok.ipynb` and run the cells.

## CLI Usage (Optional)
Run the extractor without the notebook:
```bash
python run_extractor.py --username kimkardashian --max-videos 10 --days-back 90 --include-comments
```


## Usage (Notebook)
The notebook imports `tiktok_extractor.py`, loads credentials from environment variables, and runs an extraction with configurable parameters.

## Output
- Extracted JSON files named like `username_FULL_DATA_YYYYMMDD_HHMMSS.json`.
- Daily request usage log in `tiktok_api_usage_log.json`.

Both outputs are excluded from version control via `.gitignore`.

## Best Practices Showcased
- Secrets are never hard-coded (environment variables only).
- Separation of concerns: reusable extraction module + notebook orchestration.
- Logging, parameterization, and clear configuration blocks.
- Reproducible workflow with explicit dependencies.

## Notes
- **Security**: Keep `.env` out of version control. `.env.example` should only contain placeholders, never real keys.
- If keys are ever shared or committed, rotate them immediately.
- This project uses the TikTok Research API and respects its rate limits and access policies.
- Always follow applicable terms of service and data privacy requirements.
