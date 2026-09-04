"""
Stages 3 & 4: Candidate Verification & Match Selection Pipeline
Fetches candidate images from reverse-search results, re-runs face detection/encoding,
computes Cosine Similarity and Euclidean Distance metrics against the input face,
and filters/ranks candidates to select genuine matching social media posts.
"""

import os
import re
import io
import requests
import numpy as np
from PIL import Image
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pipeline.face_encode import FaceEncoder, FaceEncodingResult, get_face_encoder
from pipeline.reverse_search import SearchCandidate


@dataclass
class VerifiedCandidate:
    candidate: SearchCandidate
    is_match: bool
    cosine_similarity: float
    euclidean_distance: float
    similarity_score_bps: int  # 0 to 10000 basis points (e.g., 9425 = 94.25%)
    candidate_image_sha256: str = ""
    candidate_bbox: Optional[Tuple[float, float, float, float]] = None
    verification_notes: str = ""


@dataclass
class VerificationReport:
    total_candidates: int
    evaluated_candidates: int
    matches_found: int
    best_match: Optional[VerifiedCandidate] = None
    all_evaluated: List[VerifiedCandidate] = None


def fetch_candidate_image(
    image_url: Optional[str],
    source_url: Optional[str]
) -> Optional[Image.Image]:
    """
    Download candidate image from direct URL, thumbnail, or scrape og:image from webpage.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }

    # 1. Try direct image URL
    if image_url:
        try:
            resp = requests.get(image_url, headers=headers, timeout=10)
            if resp.status_code == 200 and len(resp.content) > 500:
                img = Image.open(io.BytesIO(resp.content)).convert("RGB")
                return img
        except Exception:
            pass

    # 2. Try scraping OpenGraph image from source_url
    if source_url:
        try:
            resp = requests.get(source_url, headers=headers, timeout=8)
            if resp.status_code == 200:
                html = resp.text
                og_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                if not og_match:
                    og_match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', html, re.IGNORECASE)
                
                if og_match:
                    og_url = og_match.group(1)
                    img_resp = requests.get(og_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200 and len(img_resp.content) > 500:
                        return Image.open(io.BytesIO(img_resp.content)).convert("RGB")
        except Exception:
            pass

    return None


def calculate_similarity(
    embedding1: np.ndarray,
    embedding2: np.ndarray
) -> Tuple[float, float, int]:
    """
    Compute Cosine Similarity, Euclidean Distance, and Basis Points (0 - 10000).
    Embeddings are already L2 normalized.
    """
    # Cosine similarity for unit vectors is simply dot product
    cos_sim = float(np.dot(embedding1, embedding2))
    # Clip between -1 and 1
    cos_sim = max(-1.0, min(1.0, cos_sim))

    # Euclidean distance
    euc_dist = float(np.linalg.norm(embedding1 - embedding2))

    # Convert cosine similarity to 0-10000 basis points score
    # Cosine sim typically ranges from 0.0 (unrelated) to 1.0 (identical) for faces
    score_pct = max(0.0, cos_sim) * 10000.0
    bps = int(round(score_pct))
    bps = max(0, min(10000, bps))

    return cos_sim, euc_dist, bps


class CandidateVerifier:
    def __init__(
        self,
        similarity_threshold: float = 0.60,
        encoder: Optional[FaceEncoder] = None
    ):
        """
        similarity_threshold: Minimum cosine similarity required to confirm a face match (default: 0.60)
        """
        self.similarity_threshold = similarity_threshold
        self.encoder = encoder or get_face_encoder()

    def verify_candidates(
        self,
        target_embedding: np.ndarray,
        candidates: List[SearchCandidate]
    ) -> VerificationReport:
        """
        Evaluate all candidate search results by re-encoding their faces and comparing distances.
        """
        evaluated: List[VerifiedCandidate] = []

        for cand in candidates:
            # 1. Fetch image
            cand_img = fetch_candidate_image(cand.image_url or cand.thumbnail_url, cand.source_url)
            if cand_img is None:
                evaluated.append(
                    VerifiedCandidate(
                        candidate=cand,
                        is_match=False,
                        cosine_similarity=0.0,
                        euclidean_distance=2.0,
                        similarity_score_bps=0,
                        verification_notes="Could not download candidate image"
                    )
                )
                continue

            # 2. Run Face Detection & Encoding on candidate image
            cand_result: FaceEncodingResult = self.encoder.detect_and_encode(cand_img)

            if not cand_result.has_face or cand_result.embedding is None:
                evaluated.append(
                    VerifiedCandidate(
                        candidate=cand,
                        is_match=False,
                        cosine_similarity=0.0,
                        euclidean_distance=2.0,
                        similarity_score_bps=0,
                        candidate_image_sha256=cand_result.image_sha256,
                        verification_notes="No face detected in candidate image"
                    )
                )
                continue

            # 3. Compute Distance Metrics
            cos_sim, euc_dist, bps = calculate_similarity(target_embedding, cand_result.embedding)

            is_match = (cos_sim >= self.similarity_threshold)
            notes = (
                f"Face matched with {cos_sim:.2%} similarity"
                if is_match else
                f"Below threshold ({cos_sim:.2%} < {self.similarity_threshold:.2%})"
            )

            evaluated.append(
                VerifiedCandidate(
                    candidate=cand,
                    is_match=is_match,
                    cosine_similarity=cos_sim,
                    euclidean_distance=euc_dist,
                    similarity_score_bps=bps,
                    candidate_image_sha256=cand_result.image_sha256,
                    candidate_bbox=cand_result.bounding_box,
                    verification_notes=notes
                )
            )

        # 4. Rank Candidates: Matching first, then highest cosine similarity
        evaluated.sort(
            key=lambda x: (1 if x.is_match else 0, x.cosine_similarity),
            reverse=True
        )

        matches = [c for c in evaluated if c.is_match]
        best_match = matches[0] if matches else None

        return VerificationReport(
            total_candidates=len(candidates),
            evaluated_candidates=len(evaluated),
            matches_found=len(matches),
            best_match=best_match,
            all_evaluated=evaluated
        )
