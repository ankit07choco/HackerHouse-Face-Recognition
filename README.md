# Face ID + Blockchain Verification Pipeline

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Blockchain](https://img.shields.io/badge/Blockchain-Polygon%20Amoy%20Testnet-8247e5.svg)](https://amoy.polygonscan.com/)
[![EVM Smart Contract](https://img.shields.io/badge/Solidity-0.8.20-363636.svg)](https://soliditylang.org/)
[![Face Recognition](https://img.shields.io/badge/Biometrics-MTCNN%20%2B%20InceptionResnetV1-ff6f00.svg)](https://github.com/timesler/facenet-pytorch)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An end-to-end biometric Face ID verification pipeline that takes an input photo, detects and extracts a 512-dimensional unit face embedding using MTCNN & Inception-ResNet-v1 (VGGFace2), queries live reverse-image search (Google Lens via SerpApi) to discover genuine online/social media posts, verifies candidate post images through programmatic biometric distance metrics (Cosine Similarity & Euclidean Distance), and permanently records the tamper-evident match proof onto an EVM blockchain (`Polygon Amoy Testnet`).

---

## 🌟 Architecture & 6-Stage Pipeline

```
┌─────────────────┐
│   Input Image   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [Stage 1] Face Detection & 512-d Biometric Encoding         │
│  • MTCNN deep face detection & alignment                    │
│  • InceptionResnetV1 (VGGFace2) 512-d unit vector           │
│  • SHA-256(Raw Image) + SHA-256(Face Embedding)             │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [Stage 2] Live Reverse Image Search                         │
│  • Google Lens engine (SerpApi) live visual web search      │
│  • Extracts candidate posts, thumbnails, and social URLs    │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [Stage 3] Candidate Verification & Re-Encoding              │
│  • Fetch candidate images / OpenGraph post images           │
│  • Re-run face detection & embedding on candidates          │
│  • Compute Cosine Similarity and Euclidean Distance         │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [Stage 4] Match Selection & Ranking                         │
│  • Filter and rank candidates by similarity score           │
│  • Validate biometric threshold (cosine sim >= 60%)         │
│  • Zero false-positive enforcement                          │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [Stage 5] Blockchain Write (MatchRegistry.sol)              │
│  • Store imageHash, encodingHash, matchUrl, similarityScore │
│  • EVM Testnet Transaction (Polygon Amoy / Sepolia)         │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ [Stage 6] Verification Output & On-Chain Replay Proof       │
│  • Query smart contract view function getMatch(imageHash)   │
│  • PolygonScan transaction hash & block explorer proof      │
│  • Standalone replay CLI for independent evaluation         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

- **Production-Grade Biometrics**: Uses MTCNN for high-precision face landmark/bounding-box extraction and Inception-ResNet-v1 (pretrained on VGGFace2) for 512-dimensional unit-sphere embeddings.
- **Genuine Live Reverse-Image Search**: Queries live web indices using SerpApi Google Lens engine — no fake fixtures or hardcoded mock results.
- **Strict Zero False-Positive Policy**: If an unindexed or private photo is submitted, the pipeline cleanly reports that no match was found without forcing a false positive or modifying blockchain state.
- **Direct Web URL Recognition**: Allows uploading local files or pasting any image URL directly from the internet.
- **Smart Contract Immutability**: Custom Solidity contract (`MatchRegistry.sol`) deployed to EVM blockchain stores cryptographic hashes of the input photo, facial vector, matched URL, timestamp, and basis-point similarity score.
- **Interactive Web UI Dashboard**: Modern dark-mode web application (`http://localhost:8000`) with live face detection canvas, candidate comparison gauges, and blockchain telemetry.
- **Independent On-Chain Verification CLI**: Built-in `--verify <image_path_or_hash>` command allows anyone to query and confirm the tamper-evident on-chain record at any time.

---

## ⛓️ Blockchain Choice & Justification

| Feature | Choice: Polygon Amoy Testnet |
|---|---|
| **Network Type** | Public EVM Proof-of-Stake Testnet (Chain ID `80002`) |
| **Reasoning** | Fast block finality (~2 seconds), zero real-world gas costs via testnet faucets, full EVM smart contract compatibility. |
| **Public Explorer** | [PolygonScan Amoy Explorer](https://amoy.polygonscan.com) gives instant, transparent, public verifiability. |
| **Fallback** | Supports Ethereum Sepolia (Chain ID `11155111`) or Local In-Memory EVM for zero-setup offline evaluations. |

---

## 📋 Prerequisites & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/ayushlostvolts/HackerHouse-Face-Recognition.git
cd HackerHouse-Face-Recognition
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Using uv (recommended for fast install):
uv venv --python 3.11 .venv
.venv\Scripts\activate
uv pip install -r requirements.txt

# Or using standard python:
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure the following variables in `.env`:
```ini
# SerpApi Key for live Google Lens reverse search (get free key at https://serpapi.com/)
SERPAPI_API_KEY=your_serpapi_api_key_here

# Blockchain Network (Polygon Amoy Testnet default)
RPC_URL=https://rpc-amoy.polygon.technology/
CHAIN_ID=80002

# EVM Wallet Private Key (with testnet MATIC for gas)
PRIVATE_KEY=your_private_key_here

# Deployed Smart Contract Address (leave blank to deploy new instance)
CONTRACT_ADDRESS=

# Block Explorer Base URL
EXPLORER_URL=https://amoy.polygonscan.com
```

---

## 🏃 How to Run the Pipeline

### 1. Run Interactive Web UI Dashboard
```bash
python ui/server.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser:
- Drag & drop any portrait photo or paste any image URL from the internet.
- Configure similarity threshold (0.40 – 0.95).
- Click **"⚡ Run 6-Stage Pipeline"** to watch the end-to-end execution.

---

### 2. Run Full 6-Stage Pipeline via CLI
```bash
# Run with local image file:
python main.py sample_images/narendra_modi.jpg

# Run with custom similarity threshold:
python main.py sample_images/narendra_modi.jpg --threshold 0.70
```

You will see rich terminal output detailing every stage:
1. **Face detection** (bounding box, detection probability, image SHA-256, embedding SHA-256).
2. **Reverse search** (live candidate URLs, domains, and thumbnails).
3. **Candidate verification** (biometric comparison table, cosine similarity, euclidean distance).
4. **Match selection** (top genuine match selection).
5. **Blockchain write** (transaction submission, block number, gas used, transaction hash, explorer link).
6. **On-chain verification** (readback from `MatchRegistry.sol` contract state).

---

### 3. Independent On-Chain Replay & Verification
To verify that an image was previously matched and recorded on the blockchain without re-running reverse search:
```bash
# Verify by image file path:
python main.py --verify sample_images/narendra_modi.jpg

# Or verify directly by image SHA-256 hash:
python main.py --verify 0x6850f505f91166aec278d97edf0fe55b419110ce4c35e2680c91a183b61ae55e
```

---

### 4. Deploy MatchRegistry Smart Contract
To deploy a new instance of `MatchRegistry.sol` to Polygon Amoy or Sepolia:
```bash
python main.py --deploy
# Or:
python scripts/deploy_contract.py
```

---

## 📁 Repository Structure

```
.
├── contracts/
│   ├── MatchRegistry.sol       # Solidity smart contract
│   └── MatchRegistry.json      # Compiled ABI & Bytecode
├── pipeline/
│   ├── __init__.py
│   ├── face_encode.py          # Stage 1: MTCNN & InceptionResnetV1 encoding
│   ├── reverse_search.py       # Stage 2: SerpApi Google Lens reverse search
│   ├── verify_match.py         # Stages 3 & 4: Candidate verification & similarity scoring
│   └── blockchain_write.py     # Stages 5 & 6: Web3 blockchain write & readback
├── scripts/
│   └── deploy_contract.py      # Contract deployment script
├── sample_images/
│   ├── sample_face.jpg         # Sample test portrait
│   └── narendra_modi.jpg       # Sample test portrait
├── ui/
│   ├── server.py               # FastAPI backend server
│   └── static/
│       ├── index.html          # Web UI dashboard
│       ├── style.css           # Styling
│       └── app.js              # Frontend client application
├── .env.example                # Configuration template
├── main.py                     # Main CLI orchestrator
├── README.md                   # Complete documentation
├── requirements.txt            # Python dependencies
└── recording_link.md           # Screen recording proof link
```

---

## 🔬 Smart Contract Specification (`MatchRegistry.sol`)

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MatchRegistry {
    struct MatchRecord {
        bytes32 imageHash;          // SHA-256 of original input image
        bytes32 encodingHash;       // SHA-256 of 512-d face embedding
        string matchUrl;            // Matched social post URL
        uint256 similarityScoreBps; // Score in basis points (e.g. 9850 = 98.50%)
        uint256 timestamp;          // Block timestamp
        address recordedBy;         // Recorder wallet address
    }

    mapping(bytes32 => MatchRecord) public records;
    bytes32[] public recordedHashes;

    event MatchRecorded(
        bytes32 indexed imageHash,
        bytes32 indexed encodingHash,
        string matchUrl,
        uint256 similarityScoreBps,
        uint256 timestamp,
        address indexed recordedBy
    );

    function recordMatch(
        bytes32 _imageHash,
        bytes32 _encodingHash,
        string calldata _matchUrl,
        uint256 _similarityScoreBps
    ) external;

    function getMatch(bytes32 _imageHash) external view returns (MatchRecord memory);
}
```

---

## ⚠️ Known Limitations & Edge Cases

1. **Reverse-Image Search Index Coverage**:
   - Reverse-image search engines (Google Lens, Bing, TinEye) index public internet content. Private or protected social media accounts cannot be crawled. Returning "No genuine match found" for unindexed private photos is the expected zero false-positive behavior.
2. **API Rate Limits**:
   - SerpApi free tier provides 100 searches/month. You can paste your own key in the UI settings or `.env`.
3. **Threshold Heuristics**:
   - Cosine similarity threshold is set to `0.60` (60.0%) by default. Higher thresholds (>0.80) reduce false positives, while moderate thresholds allow for lighting and angle variations.
4. **Testnet vs Mainnet**:
   - The pipeline uses Polygon Amoy / Sepolia testnets to avoid real gas costs while providing identical cryptographic guarantees to mainnet EVM chains.
