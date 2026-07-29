import json
import re
import asyncio
import sys
import numpy as np
from canonicalizer import Canonicalizer
from module_vertex import ModuleVertex


class KnowledgeCurator(ModuleVertex):
    """The Consolidation (REM) organ — a vertex of the coarse complex K.

    Digests ephemeral evidence and promotes what survives into the permanent
    scaffold. Under Construction 3 this is also the vertex that would perform
    D-generator promotion: a composite operad sub-tree that repeatedly resolves
    conflicts gets promoted to a first-class operator — gated by VerifyOp.

    Its stalk is the batch of evidence currently being digested.
    """

    def __init__(self, db_manager, cloud_router):
        super().__init__("Curator")
        self.db = db_manager
        self.router = cloud_router
        self.canonicalizer = Canonicalizer(db_manager, cloud_router)

    def operators(self) -> list:
        return ["digest", "evaluate_acquisition", "extract_objects", "promote_to_scaffold"]
        
    async def digest_in_background(self, raw_candidates: list, user_query: str):
        """
        Background process that evaluates evidence, extracts mathematical objects,
        and integrates them into the Knowledge Graph via the Canonicalizer.
        """
        for candidate in raw_candidates:
            # 1. Evaluate Acquisition Policy
            score, metrics = await self._evaluate_acquisition(candidate, user_query)
            
            if score < 0.65:
                print(f"[-] Knowledge Curator DISCARDED '{candidate['title']}' (Score: {score:.2f})")
                continue
                
            print(f"[+] Knowledge Curator ACCEPTED '{candidate['title']}' (Score: {score:.2f}). Extracting objects...")
            
            # 2. Extract Mathematical Objects
            objects = await self._extract_mathematical_objects(candidate)
            if not objects:
                continue
                
            # 3. Canonicalize and Store
            await self.canonicalizer.canonicalize_and_store(objects)
            
            # 4. Evidence Reflection
            await self._evidence_reflection(user_query, objects)

    def compute_conflict_score(self, new_vec: list, existing_vecs: list) -> float:
        """
        The 'Cognitive FFT'.
        Uses SVD to find the principal axis of disagreement (obstruction tensor)
        between a new cognitive state and the existing topological memory.
        Returns the dominant singular value as the conflict score.
        """
        if not existing_vecs:
            return 0.0
            
        # Create a matrix where each row is a difference vector: (existing - new)
        diff_matrix = np.array(existing_vecs) - np.array(new_vec)
        
        # Run SVD
        try:
            U, S, Vt = np.linalg.svd(diff_matrix, full_matrices=False)
            # S contains the singular values. The dominant singular value
            # represents the strongest axis of logical disagreement.
            conflict_score = S[0] if len(S) > 0 else 0.0
            return float(conflict_score)
        except np.linalg.LinAlgError:
            return 0.0

    async def _evaluate_acquisition(self, candidate: dict, user_query: str) -> tuple[float, dict]:
        prompt = f"""
        Evaluate this paper for permanent integration into our Mathematical OS.
        Title: {candidate['title']}
        Abstract: {candidate['abstract']}
        Query Context: {user_query}
        
        Identify the DOMAIN. If not Mathematics, Theoretical Physics, Computer Science, Engineering, or Optimization, output DOMAIN: REJECTED.
        
        Provide scores (0.0 to 1.0):
        NOVELTY: [score]
        INFORMATION_GAIN: [score] (How much does this reduce uncertainty or fill gaps?)
        
        Format exactly:
        DOMAIN: Mathematics
        NOVELTY: 0.8
        INFORMATION_GAIN: 0.9
        """
        try:
            res = await self.router.query_frontier_brain(prompt=prompt, context="", intent="triage")
            
            domain_match = re.search(r'DOMAIN:\s*(.+)', res, re.IGNORECASE)
            domain = domain_match.group(1).strip() if domain_match else "UNKNOWN"
            
            if "REJECTED" in domain.upper() or domain == "UNKNOWN":
                return 0.0, {}
                
            metrics = {"AUTHORITY": candidate.get("authority_score", 0.5), "DOMAIN": 1.0}
            
            for key in ["NOVELTY", "INFORMATION_GAIN"]:
                match = re.search(rf'{key}:\s*([0-9\.]+)', res, re.IGNORECASE)
                metrics[key] = float(match.group(1)) if match else 0.5
                
            # AcquisitionScore = 0.4*Authority + 0.3*Novelty + 0.2*InfoGain + 0.1*Domain
            final_score = (metrics["AUTHORITY"] * 0.4) + (metrics["NOVELTY"] * 0.3) + (metrics["INFORMATION_GAIN"] * 0.2) + (metrics["DOMAIN"] * 0.1)
            
            return final_score, metrics
        except Exception as e:
            print(f"[-] Evaluation failed: {e}", file=sys.stderr)
            return 0.0, {}

    async def _extract_mathematical_objects(self, candidate: dict) -> list:
        prompt = f"""
        Extract rich Mathematical Objects from this text.
        Text: {candidate['title']} - {candidate['abstract']}
        
        Objects must be typed as one of: Definition, Theorem, Lemma, Corollary, Algorithm, Technique, Counterexample, Proof Strategy, Dependency.
        
        Output ONLY a valid JSON array of objects:
        [
          {{
            "type": "Definition",
            "title": "Sobolev Space W^1,p",
            "content": "A Banach space of functions whose weak derivatives exist and belong to L^p...",
            "dependencies": ["L^p Space", "Weak Derivative"],
            "provenance": "{candidate['publisher']}: {candidate['title']}"
          }}
        ]
        """
        try:
            res = await self.router.query_frontier_brain(prompt=prompt, context="", intent="triage")
            match = re.search(r'\[.*\]', res, re.DOTALL)
            return json.loads(match.group(0)) if match else []
        except Exception as e:
            print(f"[-] Object extraction failed: {e}", file=sys.stderr)
            return []

    async def _evidence_reflection(self, query: str, objects: list):
        """HONESTY FIX: this printed 'Evaluating the impact of N new objects on the
        graph' and then did nothing (`pass`) - announcing work it never performed.
        It now states its real status instead of narrating imaginary analysis."""
        print(f"[!] Evidence Reflection NOT IMPLEMENTED: {len(objects)} new objects were "
              f"ingested for query '{query}' but their impact on the graph was NOT evaluated.")
        return None