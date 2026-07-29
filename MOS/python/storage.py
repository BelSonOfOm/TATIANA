"""
TATIANA — persistent storage (rebuild of the missing STORAGE.database).

The legacy Librarian/Harvester/Canonicalizer/ContextManager all imported
`STORAGE.database`, which did not exist in this tree — so the entire retrieval
organ could not even import. This module rebuilds that layer against the EXACT
interface the legacy code calls, so those scripts become runnable and can then be
given coordinates as ModuleVertex organs (Phase 5 / D3).

Design rules carried over from the audit:
  * No fabricated returns. A query with no data returns empty/None, never invented
    numbers.
  * Provenance is a first-class JSON list, because merges must accumulate sources
    rather than silently overwrite them.
  * Embeddings are stored as JSON float arrays at EMBED_DIM; a dimension mismatch
    RAISES rather than being padded or truncated.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from embeddings import EMBED_DIM

# Where downloaded papers/books live. Override with TATIANA_VAULT.
VAULT_ROOT = Path(os.environ.get(
    "TATIANA_VAULT",
    Path(__file__).resolve().parent.parent / "Vault"))

DEFAULT_DB = str(Path(__file__).resolve().parent.parent / "mos_knowledge.db")


SCHEMA = """
CREATE TABLE IF NOT EXISTS semantic_nodes (
    id          TEXT PRIMARY KEY,
    node_type   TEXT,
    content     TEXT,
    provenance  TEXT DEFAULT '[]',
    confidence  REAL DEFAULT 1.0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS concept_embeddings (
    id        TEXT PRIMARY KEY,
    node_id   TEXT,
    dim       INTEGER,
    vector    TEXT,
    FOREIGN KEY(node_id) REFERENCES semantic_nodes(id)
);

-- n-ary relations ARE the simplices: a theorem plus its prerequisite closure.
CREATE TABLE IF NOT EXISTS n_ary_relations (
    id        TEXT PRIMARY KEY,
    kind      TEXT,
    arity     INTEGER,
    nodes     TEXT,
    weight    REAL DEFAULT 1.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Audit trail of every typed structural operation (bind/collapse/merge/link).
CREATE TABLE IF NOT EXISTS graph_mutations (
    id        TEXT PRIMARY KEY,
    kind      TEXT,
    target    TEXT,
    before    TEXT,
    after     TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingestion_queue (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    book_title   TEXT UNIQUE,
    local_path   TEXT,
    status       TEXT DEFAULT 'queued',
    current_page INTEGER DEFAULT 0,
    total_pages  INTEGER DEFAULT 0,
    retries      INTEGER DEFAULT 0,
    concepts     INTEGER DEFAULT 0,
    skills       INTEGER DEFAULT 0,
    updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS acquisition_queue (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    query      TEXT,
    target_url TEXT,
    title      TEXT,
    status     TEXT DEFAULT 'QUEUED'
);

CREATE TABLE IF NOT EXISTS papers (
    id    TEXT PRIMARY KEY,
    title TEXT,
    path  TEXT
);

CREATE TABLE IF NOT EXISTS semantic_bridges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_paper_id TEXT,
    target_paper_id TEXT,
    shared_concept  TEXT
);

CREATE TABLE IF NOT EXISTS category_nodes (
    id   TEXT PRIMARY KEY,
    name TEXT
);

CREATE TABLE IF NOT EXISTS category_edges (
    parent_id TEXT,
    child_id  TEXT,
    PRIMARY KEY (parent_id, child_id)
);

CREATE TABLE IF NOT EXISTS knowledge_objects (
    id             TEXT PRIMARY KEY,
    object_type    TEXT,
    title          TEXT,
    prerequisites  TEXT,
    statement      TEXT,
    proof_strategy TEXT,
    source_book    TEXT,
    source_pages   TEXT
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    id                TEXT PRIMARY KEY,
    name              TEXT,
    trigger_condition TEXT,
    procedure         TEXT,
    prerequisites     TEXT,
    source_book       TEXT,
    confidence        REAL DEFAULT 0.9,
    occurrences       INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS resources (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT,
    file_path TEXT,
    status    TEXT
);

CREATE TABLE IF NOT EXISTS working_memory (
    session_id        TEXT PRIMARY KEY,
    current_project   TEXT,
    current_file      TEXT,
    current_goal      TEXT,
    last_decision     TEXT,
    pending_questions TEXT,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


class DatabaseManager:
    """SQLite-backed knowledge store. Safe for use from background threads."""

    def __init__(self, db_path: str = DEFAULT_DB):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        VAULT_ROOT.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self.conn.executescript(SCHEMA)
            self.conn.commit()

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    # ------------------------------------------------------------------ core
    def execute_update(self, query: str, params: Sequence[Any] = ()) -> int:
        with self._lock:
            cur = self.conn.execute(query, params)
            self.conn.commit()
            return cur.rowcount

    def query(self, sql: str, params: Sequence[Any] = ()) -> List[sqlite3.Row]:
        with self._lock:
            return self.conn.execute(sql, params).fetchall()

    # ------------------------------------------------------- knowledge graph
    def insert_semantic_node(self, node_id: str, node_type: str, content: str,
                             provenance: str = "", confidence: float = 1.0) -> str:
        prov = json.dumps([provenance] if provenance else [])
        self.execute_update(
            "INSERT OR IGNORE INTO semantic_nodes (id, node_type, content, provenance, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (node_id, node_type, content, prov, confidence))
        return node_id

    def insert_concept_embedding(self, emb_id: str, node_id: str,
                                 vector: Sequence[float]) -> None:
        vec = [float(x) for x in vector]
        if len(vec) != EMBED_DIM:
            # Never pad/truncate geometry — see embeddings.py THE CONTRACT.
            raise ValueError(
                f"Embedding for '{node_id}' has dim {len(vec)}, expected {EMBED_DIM}.")
        self.execute_update(
            "INSERT OR REPLACE INTO concept_embeddings (id, node_id, dim, vector) "
            "VALUES (?, ?, ?, ?)",
            (emb_id, node_id, len(vec), json.dumps(vec)))

    def get_concept_embedding(self, node_id: str) -> Optional[List[float]]:
        rows = self.query(
            "SELECT vector FROM concept_embeddings WHERE node_id = ? LIMIT 1", (node_id,))
        return json.loads(rows[0]["vector"]) if rows else None

    def all_concept_embeddings(self) -> List[Tuple[str, List[float]]]:
        """(node_id, vector) for every stored concept — used for similarity search."""
        return [(r["node_id"], json.loads(r["vector"]))
                for r in self.query("SELECT node_id, vector FROM concept_embeddings")]

    def insert_n_ary_relation(self, rel_id: str, kind: str,
                              nodes: Sequence[str], weight: float = 1.0) -> None:
        """An n-ary relation IS a simplex: all listed nodes jointly bound."""
        node_list = list(nodes)
        self.execute_update(
            "INSERT OR REPLACE INTO n_ary_relations (id, kind, arity, nodes, weight) "
            "VALUES (?, ?, ?, ?, ?)",
            (rel_id, kind, len(node_list), json.dumps(node_list), weight))

    def get_relations(self, kind: Optional[str] = None) -> List[dict]:
        sql = "SELECT id, kind, arity, nodes, weight FROM n_ary_relations"
        params: Tuple = ()
        if kind:
            sql += " WHERE kind = ?"
            params = (kind,)
        return [{"id": r["id"], "kind": r["kind"], "arity": r["arity"],
                 "nodes": json.loads(r["nodes"]), "weight": r["weight"]}
                for r in self.query(sql, params)]

    def log_graph_mutation(self, mut_id: str, kind: str, target: str,
                           before: Any = None, after: Any = None) -> None:
        self.execute_update(
            "INSERT OR REPLACE INTO graph_mutations (id, kind, target, before, after) "
            "VALUES (?, ?, ?, ?, ?)",
            (mut_id, kind, target, json.dumps(before or {}), json.dumps(after or {})))

    # ------------------------------------------------------------- ingestion
    def enqueue_ingestion(self, book_title: str, local_path: str) -> None:
        self.execute_update(
            "INSERT OR IGNORE INTO ingestion_queue (book_title, local_path, status) "
            "VALUES (?, ?, 'queued')", (book_title, local_path))

    def get_next_ingestion_task(self) -> Optional[Tuple]:
        """Returns (id, book_title, local_path, current_page, total_pages,
        retries, concepts, skills) or None. Retry-exhausted items are skipped."""
        rows = self.query(
            "SELECT id, book_title, local_path, current_page, total_pages, retries, "
            "concepts, skills FROM ingestion_queue "
            "WHERE status IN ('queued','processing') AND retries < 3 "
            "ORDER BY id LIMIT 1")
        return tuple(rows[0]) if rows else None

    def update_ingestion_progress(self, task_id: int, status: str, current_page: int,
                                  total_pages: int, concepts: int, skills: int) -> None:
        self.execute_update(
            "UPDATE ingestion_queue SET status=?, current_page=?, total_pages=?, "
            "concepts=?, skills=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, current_page, total_pages, concepts, skills, task_id))

    def increment_ingestion_retry(self, task_id: int) -> None:
        self.execute_update(
            "UPDATE ingestion_queue SET retries = retries + 1, status='failed' WHERE id=?",
            (task_id,))

    def get_ingestion_metrics(self) -> Dict[str, Any]:
        """REAL counts from the database. Returns zeros when empty — never invents."""
        rows = self.query(
            "SELECT status, COUNT(*) c, SUM(concepts) con, SUM(skills) sk "
            "FROM ingestion_queue GROUP BY status")
        by_status = {r["status"]: r["c"] for r in rows}
        total_concepts = sum((r["con"] or 0) for r in rows)
        total_skills = sum((r["sk"] or 0) for r in rows)
        n_nodes = self.query("SELECT COUNT(*) c FROM semantic_nodes")[0]["c"]
        n_rel = self.query("SELECT COUNT(*) c FROM n_ary_relations")[0]["c"]
        return {
            "by_status": by_status,
            "documents": sum(by_status.values()),
            "concepts_extracted": total_concepts,
            "skills_extracted": total_skills,
            "semantic_nodes": n_nodes,
            "relations": n_rel,
        }

    # --------------------------------------------------------- working memory
    def get_working_memory_state(self, session_id: str) -> Dict[str, str]:
        rows = self.query(
            "SELECT current_project, current_file, current_goal, last_decision, "
            "pending_questions FROM working_memory WHERE session_id = ?", (session_id,))
        if not rows:
            return {}
        r = rows[0]
        return {
            "current_project": r["current_project"] or "",
            "current_file": r["current_file"] or "",
            "current_goal": r["current_goal"] or "",
            "last_decision": r["last_decision"] or "",
            "pending_questions": r["pending_questions"] or "",
        }

    def update_working_memory_state(self, session_id: str, current_project: str = "",
                                    current_file: str = "", current_goal: str = "",
                                    last_decision: str = "",
                                    pending_questions: str = "") -> None:
        self.execute_update(
            "INSERT INTO working_memory (session_id, current_project, current_file, "
            "current_goal, last_decision, pending_questions, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
            "ON CONFLICT(session_id) DO UPDATE SET current_project=excluded.current_project, "
            "current_file=excluded.current_file, current_goal=excluded.current_goal, "
            "last_decision=excluded.last_decision, "
            "pending_questions=excluded.pending_questions, updated_at=CURRENT_TIMESTAMP",
            (session_id, current_project, current_file, current_goal,
             last_decision, pending_questions))


if __name__ == "__main__":
    import tempfile

    tmp = os.path.join(tempfile.gettempdir(), "tatiana_storage_selftest.db")
    if os.path.exists(tmp):
        os.remove(tmp)
    db = DatabaseManager(tmp)

    print("VAULT_ROOT:", VAULT_ROOT)

    print("\n=== empty DB reports ZEROS, not invented numbers ===")
    print("   ", db.get_ingestion_metrics())

    print("\n=== knowledge graph ===")
    db.insert_semantic_node("hilbert_space", "definition", "A complete inner product space.",
                            "Rudin, Functional Analysis")
    db.insert_semantic_node("banach_space", "definition", "A complete normed space.", "Rudin")
    db.insert_n_ary_relation("rel_dep_hilbert", "depends_on",
                             ["hilbert_space", "banach_space"], 1.0)
    print("    relations (= simplices):", db.get_relations("depends_on"))

    print("\n=== embeddings enforce the dimension contract ===")
    db.insert_concept_embedding("emb_h", "hilbert_space", [0.0] * EMBED_DIM)
    print(f"    stored {EMBED_DIM}-d ok; retrieved len =",
          len(db.get_concept_embedding("hilbert_space")))
    try:
        db.insert_concept_embedding("emb_bad", "banach_space", [0.0] * 128)
        print("    !! ERROR: accepted a wrong-dimension vector")
    except ValueError as e:
        print("    correctly REFUSED 128-d vector:", str(e)[:60])

    print("\n=== ingestion queue ===")
    db.enqueue_ingestion("FIRST DRAFT.pdf", "/vault/FIRST DRAFT.pdf")
    task = db.get_next_ingestion_task()
    print("    next task:", task)
    db.update_ingestion_progress(task[0], "processing", 3, 10, 7, 2)
    print("    metrics now:", db.get_ingestion_metrics())

    print("\n=== working memory ===")
    db.update_working_memory_state("s1", current_project="FIRST DRAFT",
                                   current_goal="solve Section 3")
    print("   ", db.get_working_memory_state("s1"))
    print("    unknown session ->", db.get_working_memory_state("nope"), "(empty, not fabricated)")

    db.close()
    os.remove(tmp)
    print("\nstorage.py self-test complete.")
