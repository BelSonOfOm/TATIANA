# Notes for Tomorrow (Development Goals for Tatiana)

## 1. Chat Memory & User Context
- **Current Chat Memory:** Fix the system's ability to remember the context of current casual chats (e.g., remembering the user's name across turns). Currently, bypassing the Cognitive State for 'CHAT' makes her amnesiac to conversational context.
- **User Memory & Preferences:** Establish a long-term memory of the user, their preferences, and how their relationship/interactions evolve with Tatiana over time.

## 2. Memorical Simplices & Context Organization
- Develop a distinct category of "memorical simplices" that harmonize with each other to organize memories of the user, solved problems, and past conversations.
- Ensure this is done in a structured way that avoids poisoning the active problem-solving context window (the Cognitive State) with casual chat noise.

## 3. Cognitive Architecture Research
- Study how human brains cache memories (e.g., working memory vs. long-term potentiation, the biological equivalents of RAM and Cache).
- Map these biological concepts into Tatiana's topological and sheaf-theoretic architecture.

## 4. Knowledge Base Integration
- Link Tatiana to the "HDD of books and parsers".
- Design how to handle, ingest, and represent large-scale external knowledge within the mathematical operating system.

## 5. Autonomous Researcher Capabilities (Beyond Static LLM)
- **External Search & Retrieval:** Connect `SearchOp` to the internet, APIs (ArXiv, Google Scholar), and local file system so she can scavenge papers and books.
- **Tool Execution:** Upgrade the `ColibriKernel` to allow Tatiana to output commands (e.g., executing Python scripts, querying databases) that the C++ engine physically executes on her behalf.
- **Objective Verification (`VerifyOp`):** Implement a new Operad node that runs a theorem prover (like Lean/Coq) or code execution to objectively check her work. Her conflict score should spike if verification fails, keeping her in `RESOLVE` mode until the math is actually proven.
