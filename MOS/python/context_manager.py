import json
import asyncio

from module_vertex import ModuleVertex


class ContextManager(ModuleVertex):
    """The Working Memory organ — a vertex of the coarse complex K.

    Holds the active session state (project, file, goal, last decision, open
    questions). In the formalism this is the restriction of the global section s
    to the current task: what the system is working on RIGHT NOW, as opposed to
    what it knows in general.

    Its stalk is that active goal state, which is what lets Working Memory
    measurably agree or disagree with what the Librarian is retrieving.
    """

    def __init__(self, db, router):
        super().__init__("WorkingMemory")
        self.db = db
        self.router = router

    def operators(self) -> list:
        return ["update_state", "get_context_block", "inject_boundary", "drop_boundary"]

    def sync_stalk(self, session_id: str) -> None:
        """Embed the current working-memory state so this vertex has a position.

        Local embedding, so it costs no API quota. If the session has no state the
        vertex stays idle (stalk None) rather than being given a fake position.
        """
        from embeddings import embed
        state = self.db.get_working_memory_state(session_id)
        if not state:
            return
        text = " ".join(v for v in state.values() if v)
        if not text.strip():
            return
        self.release()
        self.hold(f"working_memory:{session_id}", embed(text))

    async def update_state(self, session_id: str, new_message: str):
        # We fetch the old state
        old_state = self.db.get_working_memory_state(session_id)
        
        prompt = f"""
        Extract the current working memory state from the user's latest message.
        Update the old state with any new information.
        
        Old State:
        {json.dumps(old_state)}
        
        Latest Message:
        "{new_message}"
        
        Output MUST be valid JSON with keys: current_project, current_file, current_goal, last_decision, pending_questions.
        """
        try:
            res = await self.router.query_frontier_brain(prompt, context="", intent="triage")
            # Extract JSON from res
            start = res.find('{')
            end = res.rfind('}')
            if start != -1 and end != -1:
                new_state = json.loads(res[start:end+1])
                
                def _to_str(v):
                    if isinstance(v, (list, dict)): return json.dumps(v)
                    return str(v) if v is not None else ""
                    
                self.db.update_working_memory_state(
                    session_id,
                    _to_str(new_state.get("current_project", "")),
                    _to_str(new_state.get("current_file", "")),
                    _to_str(new_state.get("current_goal", "")),
                    _to_str(new_state.get("last_decision", "")),
                    _to_str(new_state.get("pending_questions", ""))
                )
        except Exception as e:
            import sys
            print(f"[-] ContextManager update failed: {e}", file=sys.stderr)

    def get_context_block(self, session_id: str) -> str:
        state = self.db.get_working_memory_state(session_id)
        if not state:
            return ""
        
        return f"""
[WORKING MEMORY STATE]
Project: {state.get('current_project', 'None')}
File: {state.get('current_file', 'None')}
Goal: {state.get('current_goal', 'None')}
Decision: {state.get('last_decision', 'None')}
Pending: {state.get('pending_questions', 'None')}
"""
