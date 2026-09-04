# PRD: Face ID + Blockchain Verification Pipeline

**Task Reference:** Task #3 — Face ID + Blockchain Verification
**Deadline:** Sep 7, 11:59 PM IST
**Document Owner:** Ayush (DevAi Studios)
**Status:** Draft v1.0

---

## 1. Problem Statement

Build a pipeline that takes a photo, detects and encodes the face in it, finds a genuine matching social media post through real reverse-image search (not a hardcoded/mocked result), and writes that match's data to a blockchain to create a tamper-evident, verifiable record of the match.

The deliverable is the **pipeline itself** — a runnable script/tool, not a hosted website. Judging is based on functionality, code quality, and an unedited end-to-end screen recording.

---

## 2. Goals

| Goal | Success Criterion |
|---|---|
| Face detection & encoding | Given an input image, reliably detect a face and produce a numerical embedding/encoding |
| Genuine reverse-image search | Query a real reverse-image search provider (not scraped/faked) and retrieve candidate social posts |
| Real match validation | At least one retrieved candidate is a genuine matching social media post — verified programmatically, not hardcoded |
| Blockchain write | Match metadata is written to a blockchain (testnet acceptable) producing a verifiable, tamper-evident record |
| Reproducibility | Anyone can clone the repo and run the pipeline end-to-end using the README |
| Transparent limitations | README documents what does/doesn't work, and known edge cases |

### Non-Goals
- No frontend/website required — CLI or notebook is sufficient
- No production-scale uptime/hosting requirements
- No need to support every social platform — one or two is fine, if genuinely queried

---

## 3. Users & Judging Context

- **Primary user:** Evaluator/judge running the pipeline locally or watching the screen recording
- **Implication:** Prioritize clarity of run instructions, deterministic/logged output, and visible proof of each pipeline stage (not just a final "match found" message) — judges need to see the mechanism, not just the result.

---

## 4. Pipeline Architecture

```
Input Image
    │
    ▼
[1] Face Detection & Encoding
    │  (bounding box + 128/512-d embedding)
    ▼
[2] Reverse Image Search (real API/service)
    │  (candidate URLs + thumbnails)
    ▼
[3] Candidate Verification
    │  (re-run face detection on candidates,
    │   compare embeddings via distance metric,
    │   filter by similarity threshold)
    ▼
[4] Match Selection
    │  (pick best-scoring genuine match; log confidence)
    ▼
[5] Blockchain Write
    │  (hash image + match metadata, submit tx)
    ▼
[6] Verification Output
       (tx hash / explorer link + on-chain record readout)
```

### 4.1 Stage 1 — Face Detection & Encoding
- **Library options:** `face_recognition` (dlib-based, simplest), `DeepFace`, `InsightFace`, or a cloud API (AWS Rekognition, Azure Face)
- **Recommendation:** `face_recognition` for local/offline speed and zero API cost during dev; swap to `InsightFace` if higher accuracy is needed for lookalike disambiguation
- **Output:** face bounding box, 128-d (or model-specific) encoding vector, confidence score
- **Edge cases:** no face detected, multiple faces (require user to select/crop or auto-pick largest face), low-resolution input

### 4.2 Stage 2 — Reverse Image Search (must be genuine, no hardcoding)
- **Candidate providers:**
  - **SerpApi (Google Lens/Reverse Image Search)** — has a proper API, straightforward integration, free-tier available for demo purposes
  - **Bing Visual Search API**
  - **PimEyes** (face-search specific, but paid/restricted — flag licensing risk)
  - **TinEye API**
- **Recommendation:** SerpApi's Google Lens endpoint — most reliable general-purpose reverse image search with structured JSON results including source URLs
- **Process:** upload/host the input image temporarily (or pass URL), call API, parse returned result URLs, filter to social media domains (instagram.com, twitter.com/x.com, facebook.com, linkedin.com, etc.)
- **Note on "genuine, no hardcoded results":** the pipeline must actually call the live API each run and use its real response — no cached/mocked fixture standing in for a live call, and no pre-selected "known good" demo image with a pre-baked answer.

### 4.3 Stage 3 — Candidate Verification
- For each candidate social post URL returned by reverse-image search:
  1. Fetch the image from that post (scrape og:image or thumbnail)
  2. Run the same face detection/encoding on it
  3. Compute distance (Euclidean or cosine) between original encoding and candidate encoding
  4. Accept as a match if distance is below a defined threshold (e.g., `face_recognition` default tolerance 0.6)
- **Why this stage matters:** reverse image search can return visually similar but non-matching images (same scene, different person); this stage is what makes the match "real" rather than "first search result."

### 4.4 Stage 4 — Match Selection
- Rank verified candidates by similarity score
- Select top match; log all candidates and scores (for transparency in the recording/README)
- If zero candidates pass threshold → pipeline reports "no genuine match found" rather than forcing a false positive

### 4.5 Stage 5 — Blockchain Write
- **Chain choice:** use a public testnet to avoid real gas costs — **Polygon Amoy testnet** or **Ethereum Sepolia** are good defaults; Solana Devnet is a lighter-weight alternative if avoiding EVM tooling
- **What gets written on-chain:**
  - SHA-256 hash of the input image (not the raw image — keep chain data minimal)
  - SHA-256 hash or short representation of the face encoding
  - Matched post URL (or hash of it, if URL length/privacy is a concern)
  - Similarity/confidence score
  - Timestamp
- **Implementation options:**
  - Simple: send the metadata as a JSON payload in a transaction's `data` field on an EVM testnet via `web3.py` or `ethers.js`
  - More structured: deploy a minimal smart contract (`recordMatch(bytes32 imageHash, string matchUrl, uint256 score)`) using Solidity + Hardhat/Foundry, then call it
- **Recommendation:** minimal smart contract is worth the extra effort — it demonstrates actual on-chain data structure rather than just a raw tx, and makes "verifiable record" easy to prove (anyone can call a public `getRecord()` view function)
- **Output:** transaction hash + block explorer link (e.g., Amoy PolygonScan) so the record is independently verifiable by the judge

### 4.6 Stage 6 — Verification Output
- Final CLI output should print:
  - Match found: Y/N
  - Matched URL + confidence score
  - Transaction hash + explorer link
  - A short "replay" command/flag to re-fetch and display the on-chain record for proof

---

## 5. Tech Stack Recommendation

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python | Best ecosystem for face-detection libs; team has existing Python backend experience |
| Face detection/encoding | `face_recognition` (or `InsightFace` for higher accuracy) | Mature, well-documented, fast local inference |
| Reverse image search | SerpApi (Google Lens engine) | Real API, structured results, generous free tier for demo |
| Image hosting for search calls | Temporary upload to a free image host (e.g., imgbb API) or local tunneling if API requires public URL | Needed because most reverse-image APIs require a URL, not raw bytes |
| Blockchain | Polygon Amoy testnet + Solidity contract, `web3.py` for interaction | No real cost, fast confirmation, PolygonScan gives instant public verifiability |
| Orchestration | Single Python script or Jupyter notebook with clear numbered cells/functions per stage | Matches "pipeline" framing and makes the screen recording easy to narrate |
| Config/secrets | `.env` file (SerpApi key, wallet private key, RPC URL) — excluded via `.gitignore` | Standard practice, keeps secrets out of the public repo |

---

## 6. Repository Deliverables (per task requirements)

```
/repo-root
 ├── README.md              → functionality, setup, how to run, which blockchain, limitations
 ├── requirements.txt
 ├── .env.example
 ├── pipeline/
 │    ├── face_encode.py
 │    ├── reverse_search.py
 │    ├── verify_match.py
 │    └── blockchain_write.py
 ├── contracts/              (if smart contract route)
 │    └── MatchRegistry.sol
 ├── main.py                 → runs full pipeline end-to-end
 ├── sample_images/          → 1–2 test images (with rights to use / synthetic)
 └── recording_link.md       → link to unedited screen recording
```

### README must explicitly cover:
1. What the pipeline does, stage by stage
2. Exact setup + run commands
3. Which blockchain/testnet is used and why
4. Known limitations (e.g., reverse-image search coverage is provider-dependent, face matching accuracy limits, testnet vs mainnet caveat, rate limits on free API tier)

---

## 7. Known Risks / Limitations to Document Upfront

- **Reverse-image search coverage**: no provider indexes all social platforms equally; a genuine "no match found" is a valid and expected outcome for many test images, not a bug.
- **API rate limits**: free-tier SerpApi/imgbb usage caps could interrupt a live demo — worth noting fallback behavior.
- **Face match false positives/negatives**: encoding-distance thresholds are heuristic; document the chosen threshold and why.
- **Privacy/ethical consideration**: worth a short README note that this is a demo pipeline using consenting/test images, not a real-world surveillance tool — reviewers may look favorably on this being addressed proactively.
- **Testnet vs mainnet**: using testnet avoids gas costs but should be clearly labeled so it's not mistaken for a production claim.

---

## 8. Milestones (given ~3 days remaining)

| Day | Milestone |
|---|---|
| Day 1 | Face detection/encoding working locally; SerpApi reverse search returning real candidate URLs |
| Day 2 | Candidate verification logic (re-encode + compare) working; blockchain contract deployed to testnet, basic write/read working |
| Day 3 | Full pipeline wired end-to-end; README written; screen recording captured unedited; repo cleaned and pushed |

---

## 9. Definition of Done

- [ ] Running `main.py <image_path>` executes all 6 stages without manual intervention
- [ ] Reverse-image search calls a live API each run (verifiable in code — no cached fixtures)
- [ ] At least one test run produces a genuine verified match with a real social post URL
- [ ] Match data is confirmed on-chain via a public block explorer link
- [ ] README covers functionality, run instructions, blockchain choice, and limitations
- [ ] Unedited screen recording captures the full run, start to finish, including the on-chain verification step
