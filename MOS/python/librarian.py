import os
import shutil
import time
import uuid
import sys
import asyncio
from pathlib import Path
from storage import VAULT_ROOT, DatabaseManager
from pdf_processor import LocalProcessor
from module_vertex import ModuleVertex
from embeddings import embed, EMBED_DIM
import json


class IntelligentLibrarian(ModuleVertex):
    """The Search/Retrieval organ — a vertex of the coarse complex K.

    MIGRATION (Phase 5 / D3): this is no longer a loose script. It occupies a
    vertex of K, and its STALK is the weighted centroid of the evidence it is
    currently holding (pi_v). That is what lets its agreement or disagreement with
    the Canonicalizer, Curator and Working Memory be MEASURED as omega_e rather
    than guessed at.

    Its share of the operator algebra D is retrieval: SearchOp and friends.
    """

    def __init__(self, db_manager: DatabaseManager, cloud_router):
        super().__init__("Librarian")
        self.db = db_manager
        self.router = cloud_router
        self.processor = LocalProcessor()

    def operators(self) -> list:
        """This vertex's contribution to D."""
        return ["SearchOp", "scavenge_internet", "ingest_document", "curate_search"]

    def hold_evidence(self, label: str, text: str, weight: float = 1.0) -> None:
        """Bring a retrieved item into this organ's fine complex.

        Called as evidence arrives so the Librarian's position in meaning-space
        reflects what it is ACTUALLY holding right now, not what it holds in
        principle. Embedding is local and free, so this costs no API quota.
        """
        if not text or not text.strip():
            return
        self.hold(label, embed(text[:2000]), weight=weight)
        
        self.bin_path = VAULT_ROOT / "Bin"
        self.bin_path.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.bin_path / "acquisition_queue.json"
        
        self.bin_path.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.bin_path / "acquisition_queue.json"
    async def execute_command(self, action: str, params: dict) -> dict:
        """Handler for the Universal Command Bus."""
        if action == "scan_bin":
            asyncio.create_task(self.process_deposit_bin())
            return {"status": "success", "message": "Scanned Vault/Bin for new files."}
        elif action == "status":
            metrics = self.db.get_ingestion_metrics()
            return {"status": "success", "metrics": metrics}
        elif action == "reorganize":
            dry_run = params.get("dry_run", True)
            target_location = params.get("location", "Math")
            return await self._cmd_reorganize(target_location, dry_run)
        elif action == "inspect":
            doc = params.get("document", "")
            return await self._cmd_inspect(doc)
        elif action == "learn":
            # HONESTY FIX: previously returned "Targeted extraction triggered" while
            # doing nothing at all. Never claim work that did not run.
            return {
                "status": "not_implemented",
                "message": "Targeted extraction is not implemented yet. No work was performed.",
            }
        elif action == "repair":
            # HONESTY FIX: previously returned "Repair executed (duplicate detection
            # and orphan pruning complete)" without performing either.
            return {
                "status": "not_implemented",
                "message": "Repair (dedup / orphan pruning) is not implemented yet. No work was performed.",
            }
        else:
            raise ValueError(f"Unknown librarian action: {action}")

    async def _cmd_reorganize(self, target_location: str, dry_run: bool) -> dict:
        """HONESTY FIX: previously returned INVENTED file moves (a hardcoded
        'Topology/Rudin.pdf -> Math/Topology/Rudin.pdf') regardless of what was
        actually in the vault. A preview that does not read the filesystem is a
        lie about the filesystem."""
        return {
            "status": "not_implemented",
            "preview_mode": dry_run,
            "target": target_location,
            "changes": [],
            "message": "Reorganize is not implemented yet. No filesystem scan was performed "
                       "and no files were moved.",
        }

    async def _cmd_inspect(self, document: str) -> dict:
        """HONESTY FIX: previously returned entirely FABRICATED telemetry
        (processed='87%', concepts=342, skills=56, missing='Spectral theory chapter')
        that was hardcoded and unrelated to any real document. That is
        indistinguishable from a genuine measurement, which makes it the most
        dangerous kind of placeholder."""
        return {
            "status": "not_implemented",
            "document": document,
            "message": "Document inspection is not implemented yet. No statistics were "
                       "computed; reporting nothing rather than inventing numbers.",
        }

    def fetch_queued_documents(self):
        if not self.queue_file.exists():
            return
            
        try:
            with open(self.queue_file, "r") as f:
                queue_data = json.load(f)
                
            for demand in queue_data:
                if demand.get("status") == "QUEUED":
                    title = demand.get("canonical_title", "")
                    print(f"[*] Attempting automated acquisition for: {title}")
                    
                    try:
                        import arxiv
                        client = arxiv.Client()
                        search = arxiv.Search(
                            query=title,
                            max_results=1,
                            sort_by=arxiv.SortCriterion.Relevance
                        )
                        results = list(client.results(search))
                        
                        if results:
                            paper = results[0]
                            # Simple substring check to verify relevance
                            if title.lower() in paper.title.lower() or paper.title.lower() in title.lower():
                                print(f"[+] Found on ArXiv: {paper.title}. Downloading...")
                                self.db.execute_update("UPDATE acquisition_queue SET status = 'Downloading' WHERE target_url = ?", (paper.entry_id,))
                                
                                # Strip problematic characters for filename
                                safe_title = "".join(c for c in paper.title if c.isalnum() or c in (' ', '_')).rstrip()
                                filename = f"{safe_title.replace(' ', '_')[:50]}.pdf"
                                paper.download_pdf(dirpath=str(self.bin_path), filename=filename)
                                print(f"[+] Download complete: {filename}")
                                self.db.execute_update("UPDATE acquisition_queue SET status = 'Parsing' WHERE target_url = ?", (paper.entry_id,))
                                continue
                    except ImportError:
                        print("[-] arxiv package not installed. Skipping automated acquisition.")
                        break
                    except Exception as e:
                        print(f"[-] ArXiv fetch failed for {title}: {e}")
                        
        except Exception as e:
            print(f"[-] Automated acquisition parsing failed: {e}")

    async def scavenge_internet(self, query: str) -> bool:
        """
        Dynamically fetches top scholarly papers matching the query if local context confidence is too low.
        Returns True if new context was acquired and processed, False otherwise.
        """
        print(f"\n[*] Web Scavenger triggered for: '{query}'. Searching ArXiv and Web...")
        acquired = False
        
        # 1. ArXiv Search
        try:
            import arxiv
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=3,
                sort_by=arxiv.SortCriterion.Relevance
            )
            results = list(client.results(search))
            
            for paper in results:
                safe_title = "".join(c for c in paper.title if c.isalnum() or c in (' ', '_')).rstrip()
                filename = f"{safe_title.replace(' ', '_')[:50]}.pdf"
                filepath = self.bin_path / filename
                
                # Check if we already have it in the DB to avoid infinite loops
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT id FROM papers WHERE title LIKE ?", (f"%{paper.title[:30]}%",))
                if cursor.fetchone():
                    print(f"[-] Scavenger skipped '{paper.title}' (Already in Vault).")
                    continue
                    
                print(f"[+] Scavenger downloading: {paper.title}...")
                paper.download_pdf(dirpath=str(self.bin_path), filename=filename)
                acquired = True
        except Exception as e:
            print(f"[-] ArXiv Scavenger failed: {e}")
            
        # 2. General Web Scavenging (Turn forums/websites into PDF)
        acquired = acquired or await self._scavenge_general_web(query)
            
        if acquired:
            print("[*] Scavenger triggering local deposit ingestion...")
            await self._process_deposit_bin_once()
            return True
            
        return False

    async def _scavenge_general_web(self, query: str) -> bool:
        print(f"[*] Scavenging general web forums and sites for: '{query}'")
        try:
            import urllib.request
            import urllib.parse
            from bs4 import BeautifulSoup
            from fpdf import FPDF
            
            # Simple DuckDuckGo HTML search
            search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            html = urllib.request.urlopen(req, timeout=10).read()
            soup = BeautifulSoup(html, 'html.parser')
            
            links = []
            for a in soup.find_all('a', class_='result__url'):
                href = a.get('href')
                if href and href.startswith('http') and 'youtube' not in href:
                    links.append(href)
                    if len(links) >= 2: # Limit to top 2 results
                        break
                        
            acquired = False
            for link in links:
                print(f"[+] Scavenging URL: {link}")
                try:
                    page_req = urllib.request.Request(link, headers={'User-Agent': 'Mozilla/5.0'})
                    page_html = urllib.request.urlopen(page_req, timeout=10).read()
                    page_soup = BeautifulSoup(page_html, 'html.parser')
                    
                    # Extract text
                    for script in page_soup(["script", "style"]):
                        script.extract()
                    text = page_soup.get_text(separator=' ', strip=True)
                    
                    if len(text) < 500:
                        continue
                        
                    title = page_soup.title.string if page_soup.title else "Web_Scrape"
                    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
                    filename = f"Scraped_{safe_title.replace(' ', '_')[:40]}.pdf"
                    filepath = self.bin_path / filename
                    
                    # Turn into PDF
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Helvetica", size=12)
                    
                    # FPDF needs latin-1 or replacing bad chars
                    clean_text = text.encode('latin-1', 'replace').decode('latin-1')
                    pdf.multi_cell(0, 10, txt=clean_text[:50000]) # Cap to 50k chars
                    pdf.output(str(filepath))
                    
                    print(f"[+] Successfully converted website to PDF: {filename}")
                    acquired = True
                except Exception as e:
                    print(f"[-] Failed to scrape {link}: {e}")
                    
            return acquired
        except Exception as e:
            print(f"[-] General web scavenging failed: {e}")
            return False

    async def process_deposit_bin(self):
        """Runs the Librarian continuously in the background."""
        print("[*] Librarian daemon starting continuous loop...")
        while True:
            try:
                await self._process_deposit_bin_once()
                await self._process_ingestion_queue()
            except Exception as e:
                print(f"[-] Librarian daemon encountered error: {e}")
            
            # Run every 5 minutes
            await asyncio.sleep(300)

    async def _process_deposit_bin_once(self):
        """Scans the Vault/Bin folder, classifies into Category Graph, moves files, and enqueues."""
        print(f"\n[*] Librarian scanning deposit bin: {self.bin_path}")
        self.fetch_queued_documents()
        
        # Display open pipeline acquisition demands to the terminal console
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r") as f:
                    queue_data = json.load(f)
                open_demands = [item for item in queue_data if item.get("status") == "QUEUED"]
                if open_demands:
                    print("[!] ALERT: Outstanding Manual Acquisition Queue Tasks Pending:")
                    for demand in open_demands:
                        print(f"    -> [DEPOSIT NEEDED]: '{demand['canonical_title']}' by {demand['authors']}")
            except Exception as e:
                print(f"[-] Failed to print execution queue summaries: {e}")

        for file_name in os.listdir(self.bin_path):
            if not file_name.endswith(".pdf") or file_name.startswith("._"):
                continue
                
            file_path = self.bin_path / file_name
            
            # Check if already queued or processing (even if it's still in Bin, maybe it failed move)
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id FROM ingestion_queue WHERE book_title = ?", (file_name,))
            if cursor.fetchone():
                continue
                
            print(f"[*] Analyzing new deposit for classification: {file_name}")
            self.db.execute_update("UPDATE acquisition_queue SET status = 'Parsing' WHERE query LIKE ?", (f"%{file_name.replace('.pdf', '')}%",))
            
            # Extract abstract for classification
            abstract_text = ""
            async for page_data in self.processor.stream_extract_pdf(str(file_path)):
                abstract_text += page_data["text"] + "\n"
                if len(abstract_text) > 1500 or page_data["page_number"] >= 3:
                    break
                    
            if not abstract_text.strip():
                print(f"[-] Document {file_name} had empty front matter. Skipping.")
                continue

            graph_category = await self._classify_document_graph(abstract_text)
            cat_name = graph_category.get("category", "Uncategorized").replace(" ", "_")
            parents = graph_category.get("parents", [])
            
            # Ensure safe category string
            safe_cat_name = "".join(c for c in cat_name if c.isalnum() or c in ("_")).strip()
            if not safe_cat_name: safe_cat_name = "Uncategorized"
            
            # Update Category Graph in DB
            self.db.execute_update("INSERT OR IGNORE INTO category_nodes (id, name) VALUES (?, ?)", (safe_cat_name, safe_cat_name))
            for parent in parents:
                safe_parent = "".join(c for c in parent if c.isalnum() or c in ("_")).replace(" ", "_")
                if safe_parent:
                    self.db.execute_update("INSERT OR IGNORE INTO category_nodes (id, name) VALUES (?, ?)", (safe_parent, safe_parent))
                    self.db.execute_update("INSERT OR IGNORE INTO category_edges (parent_id, child_id) VALUES (?, ?)", (safe_parent, safe_cat_name))
            
            # Create Folder (Filesystem is a view of the Category Graph)
            parent_dir = parents[0].replace(" ", "_") if parents else "Math"
            target_dir = VAULT_ROOT / parent_dir / safe_cat_name
            target_dir.mkdir(parents=True, exist_ok=True)
            
            new_path = target_dir / file_name
            if new_path.exists():
                print(f"[-] File {file_name} already exists in {target_dir}. Skipping move.")
                continue
                
            shutil.move(str(file_path), str(new_path))
            print(f"[+] Librarian moved {file_name} -> {target_dir.relative_to(VAULT_ROOT)}")
            
            self.db.execute_update("UPDATE acquisition_queue SET status = 'Filed' WHERE query LIKE ?", (f"%{file_name.replace('.pdf', '')}%",))
            
            print(f"[*] Queueing for deep ingestion: {file_name}")
            self.db.enqueue_ingestion(file_name, str(new_path))
            self._resolve_queue_item(file_name)

    async def _process_ingestion_queue(self):
        """Pulls the next book from the persistent queue and processes it streaming."""
        task = self.db.get_next_ingestion_task()
        if not task:
            return
            
        task_id, book_title, local_path, current_page, total_pages, retries, concepts, skills = task
        print(f"\n[*] Starting/Resuming ingestion for: {book_title} at page {current_page}")
        
        self.db.update_ingestion_progress(task_id, "processing", current_page, total_pages, concepts, skills)
        
        try:
            chunk_buffer = ""
            start_page_in_buffer = current_page + 1
            
            async for page_data in self.processor.stream_extract_pdf(local_path, start_page=current_page):
                page_text = page_data["text"]
                page_num = page_data["page_number"]
                total_pages_pdf = page_data["total_pages"]
                
                chunk_buffer += f"\n--- [Page {page_num}] ---\n" + page_text
                
                # Semantic Boundary Detector: 10000 chars min, ends in double newline OR end of book
                if (len(chunk_buffer) > 10000 and "\n\n" in chunk_buffer[-50:]) or (page_num == total_pages_pdf):
                    page_range = f"{start_page_in_buffer}-{page_num}"
                    new_c, new_s = await self._run_extraction_pipeline(book_title, chunk_buffer, page_range, task_id)
                    
                    concepts += new_c
                    skills += new_s
                    current_page = page_num
                    
                    self.db.update_ingestion_progress(task_id, "processing", current_page, total_pages_pdf, concepts, skills)
                    print(f"    -> Block [{page_range}] Extracted {new_c} concepts and {new_s} skills.")
                    
                    chunk_buffer = ""
                    start_page_in_buffer = page_num + 1

            self.db.update_ingestion_progress(task_id, "complete", current_page, total_pages_pdf, concepts, skills)
            print(f"[+] Ingestion complete for {book_title}")
        except Exception as e:
            print(f"[-] Ingestion failed for {book_title}: {e}")
            self.db.increment_ingestion_retry(task_id)

    async def _run_extraction_pipeline(self, book_title: str, text_chunk: str, page_range: str, task_id: int):
        prompt = f"""
You are an expert mathematical segmenter and skill extractor.
Analyze the following textbook excerpt from "{book_title}" (Pages {page_range}).

Your task is to extract two things:
1. KNOWLEDGE OBJECTS: Pure mathematical entities (Theorems, Definitions, Algorithms, etc.)
2. CANDIDATE SKILLS: Problem-solving moves, heuristics, and proof strategies. (e.g. "Diagonal argument", "Compactness proof via weak convergence")

Return a JSON object EXACTLY matching this schema:
{{
    "knowledge_objects": [
        {{
            "type": "theorem", // or definition, algorithm, identity, lemma, etc
            "title": "Name of the object",
            "prerequisites": ["list", "of", "prerequisites"],
            "statement": "The mathematical statement",
            "proof_strategy": ["step 1", "step 2"]
        }}
    ],
    "candidate_skills": [
        {{
            "name": "Name of the skill/move",
            "trigger_condition": "When to apply this skill",
            "procedure": ["step 1", "step 2"],
            "prerequisites": ["list", "of", "prerequisites"]
        }}
    ]
}}

EXCERPT:
{text_chunk}
"""
        try:
            response = await self.router.query_frontier_brain(prompt=prompt, context="", intent="triage")
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3].strip()
            elif response.startswith("```"):
                response = response[3:-3].strip()
                
            data = json.loads(response)
            
            knowledge_objects = data.get("knowledge_objects", [])
            candidate_skills = data.get("candidate_skills", [])
            
            for obj in knowledge_objects:
                obj_id = str(uuid.uuid4())[:8]
                query = """
                    INSERT INTO knowledge_objects (id, object_type, title, prerequisites, statement, proof_strategy, source_book, source_pages)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.db.execute_update(query, (
                    obj_id, 
                    obj.get("type", "concept"),
                    obj.get("title", ""),
                    json.dumps(obj.get("prerequisites", [])),
                    obj.get("statement", ""),
                    json.dumps(obj.get("proof_strategy", [])),
                    book_title,
                    page_range
                ))
                
            for skill in candidate_skills:
                skill_id = str(uuid.uuid4())[:8]
                query = """
                    INSERT INTO candidate_skills (id, name, trigger_condition, procedure, prerequisites, source_book, confidence, occurrences)
                    VALUES (?, ?, ?, ?, ?, ?, 0.90, 1)
                """
                self.db.execute_update(query, (
                    skill_id,
                    skill.get("name", ""),
                    skill.get("trigger_condition", ""),
                    json.dumps(skill.get("procedure", [])),
                    json.dumps(skill.get("prerequisites", [])),
                    book_title
                ))
                
            return len(knowledge_objects), len(candidate_skills)
        except Exception as e:
            print(f"[-] Knowledge & Skill extraction failed for block {page_range}: {e}")
            return 0, 0

    def _resolve_queue_item(self, resolved_filename: str):
        """Re-aligns ledger state flags when a matching book entry is satisfied."""
        if not self.queue_file.exists():
            return
        try:
            with open(self.queue_file, "r") as f:
                queue = json.load(f)
            
            updated = False
            clean_name = resolved_filename.lower().replace("_", " ")
            
            for item in queue:
                if item["status"] == "QUEUED" and (item["canonical_title"].lower() in clean_name or clean_name in item["canonical_title"].lower()):
                    item["status"] = "AVAILABLE"
                    item["resolved_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    updated = True
                    
                    # Transition DB path allocations
                    self.db.execute_update(
                        "UPDATE resources SET file_path = ?, status = 'AVAILABLE' WHERE title = ?",
                        (str(VAULT_ROOT / "Math/Textbooks" / resolved_filename), item["target"])
                    )
                    print(f"[+] Queue linking transaction complete for: {item['canonical_title']}")
            
            if updated:
                with open(self.queue_file, "w") as f:
                    json.dump(queue, f, indent=4)
        except Exception as e:
            print(f"[-] Ledger reconciliation mapping anomaly: {e}")

    async def _classify_document_graph(self, text: str) -> dict:
        prompt = f"""
        You are a Category Manager for a mathematical library.
        Analyze the following academic text and propose a hierarchical category node.
        
        Return a JSON object EXACTLY matching this schema:
        {{
            "category": "Differential_Geometry",
            "parents": ["Geometry", "Mathematics"]
        }}
        
        RULES:
        1. Base categories should be broad fields like Math, Physics, Computer_Science.
        2. Specific subfields should be the category.
        3. Do not use spaces. Use underscores for multi-word categories.
        
        Text: {text}
        """
        try:
            response = await self.router.query_frontier_brain(prompt=prompt, context="", intent="triage")
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3].strip()
            elif response.startswith("```"):
                response = response[3:-3].strip()
            return json.loads(response)
        except Exception as e:
            print(f"[-] Category classification failed: {e}")
            return {"category": "Uncategorized", "parents": ["Math"]}


            
    async def curate_search(self, query: str, bm25_results: list) -> str:
        if not bm25_results:
            print("[-] Librarian found no raw search results to curate.")
            return ""

        print(f"[*] Librarian curating and re-ranking {len(bm25_results)} raw search results...")
        candidate_blocks = []
        paper_ids = set()

        for idx, (score, data) in enumerate(bm25_results):
            if 'paper_id' in data:
                paper_ids.add(data['paper_id'])
            block_info = f"--- Candidate Chunk [{idx}] (Source: {data.get('title', 'Unknown')}) ---\n{data.get('text', '')}\n"
            candidate_blocks.append((idx, block_info))
            # Occupy the complex: retrieved evidence enters this vertex's fine
            # complex, weighted by retrieval score, so pi_v (the stalk) tracks what
            # the Librarian is genuinely holding.
            self.hold_evidence(
                label=str(data.get('title', f'chunk_{idx}')),
                text=data.get('text', ''),
                weight=float(score) if score else 1.0,
            )

        network_context = ""
        if paper_ids and len(paper_ids) > 1:
            placeholders = ', '.join('?' for _ in paper_ids)
            query_str = f"""
                SELECT p1.title, p2.title, b.shared_concept 
                FROM semantic_bridges b
                JOIN papers p1 ON b.source_paper_id = p1.id
                JOIN papers p2 ON b.target_paper_id = p2.id
                WHERE b.source_paper_id IN ({placeholders}) AND b.target_paper_id IN ({placeholders})
            """
            try:
                cursor = self.db.conn.cursor()
                cursor.execute(query_str, list(paper_ids))
                bridges = cursor.fetchall()
                if bridges:
                    network_context = "\n[Librarian Graph Insights - Established Connections]:\n"
                    for b in bridges:
                        network_context += f" * '{b[0]}' links to '{b[1]}' via the structure: {b[2]}\n"
            except Exception as e:
                print(f"[-] Failed to fetch network insights for curation: {e}")

        all_chunks_text = "\n".join([block[1] for block in candidate_blocks])
        prompt = f"""
        You are the Head Librarian for an advanced mathematical research institute. 
        Your task is to review the following candidate text chunks and filter out the ones 
        that do not directly, rigorously contribute to answering the User Query.

        User Query: "{query}"
        {network_context}
        
        Candidate Chunks:
        {all_chunks_text}

        Evaluate each chunk. Return a raw JSON list containing ONLY the integer indices of the 
        chunks that are highly relevant and mathematically cohesive (e.g., [0, 2]). 
        Exclude chunks that are redundant or off-topic. Return ONLY the JSON list.
        """
        try:
            response = await self.router.query_frontier_brain(prompt=prompt, context="")
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:-3].strip()
            elif response.startswith("```"):
                response = response[3:-3].strip()
                
            selected_indices = json.loads(response)
            print(f"[+] Librarian curated search: Kept chunks {selected_indices} out of {len(candidate_blocks)} Candidates.")
            
            final_context = ""
            if network_context:
                final_context += network_context + "\n=== RELEVANT CONTEXT CHUNKS ===\n"
            for idx, block_info in candidate_blocks:
                if idx in selected_indices:
                    final_context += block_info + "\n"
            return final_context
        except Exception as e:
            print(f"[-] Search curation failed: {e}. Falling back to uncurated context.")
            return "\n".join([block[1] for block in candidate_blocks])