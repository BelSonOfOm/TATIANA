# Mathematical Operating System (MOS) - Architecture Update

This document details the recent architectural overhaul of the Mathematical Operating System (MOS) designed to transition it from a simple reactive LLM assistant into a persistent, self-curating mathematical reasoning engine.

## 1. The Evidence Engine (Retrieval)
Instead of relying on shallow, consumer-grade web searches (like Perplexity), MOS now utilizes a mathematically rigorous `EvidenceEngine`.
- **Primary Source**: The engine pulls exclusively from high-signal academic repositories, primarily the arXiv API.
- **Scoring**: Documents are ranked locally based on Novelty, Utility, and Academic Authority before being considered.
- **Ephemeral Storage**: Papers are loaded into an `ephemeral_memory` table in the SQLite database, meaning they don't immediately pollute the core knowledge graph.

## 2. The Knowledge Curator (Digestion)
We completely repurposed the previous `harvester.py` into a `KnowledgeCurator`.
- **Purpose**: It acts as the digestion layer, decoupling *retrieval* from *knowledge integration*.
- **Extraction**: When the Core Reasoning Engine lacks confidence, the Curator digests the ephemeral evidence and extracts structured data: formal `Mathematical Objects`, `Theorems`, `Axioms`, and `Proofs`.
- **Evaluation**: It assesses the uncertainty and consensus of the extracted evidence to ensure conflicting proofs are handled gracefully.

## 3. The Canonicalizer (Graph Management)
To solve the issue of knowledge graph bloat and overlapping concepts (e.g., storing "Hilbert Space" and "Hilbert Spaces" separately), we introduced the `Canonicalizer`.
- **Deduplication**: It performs node merging and semantic clustering.
- **Curation**: Ensures that the `OSKernel` only commits curated, generalized concepts to the permanent SQLite knowledge base.

## 4. Architectural Orchestration (The Kernel & UI)
- **Non-blocking Execution**: The `OSKernel` orchestrates the retrieval and digestion loop asynchronously. The system responds to the user immediately, and if confidence is low, it triggers the Evidence Engine in the background.
- **Frontend Refactor**: Transitioned away from the heavy Tauri application framework to a lightweight, scalable web UI served directly by the FastAPI backend (`server.py`).
- **LaTeX Persistence Fix**: Resolved a critical UI regression where loading historical sessions via the `KNOWLEDGE_SYNC` websocket payload would mangle LaTeX math delimiters due to `Marked.js`. A custom `parseMarkdownWithMath()` pipeline was built to protect and flawlessly render KaTeX blocks dynamically across active streams and session history.

## Summary
The MOS is no longer just answering today's questions; it is designed to become a better mathematician over years. The flow is now explicitly separated into:
**Question** $\rightarrow$ **Evidence Engine (arXiv)** $\rightarrow$ **Immediate Answer** $\rightarrow$ *(Background)* **Knowledge Curator** $\rightarrow$ **Canonicalizer** $\rightarrow$ **Permanent Knowledge Graph**.
