## This is my Multi Agent Financial Assitance

## My check list

### Survey
- Agent: What is?
- Search Engine: DuckDuckGo
- RAG
- Memory: Document, DB handling
- Basic pipeline:
  - Reasoning though (Planing)
  - Action: use tool: search engine + RAG
  - Searching
  - Retrieval relevant document (Need a measure)
  - Embedding document (Some emb from hugging face)
  - Save to database (memory)
    - Clear temp file (if needed)
- Retrieval from RAG (search + user document)
  - User document may need PDF reader and Image reader?? (Some tool in Python PyPDF)
- Prompt conversation: {role} {context}?? ()
- Streamlit on Colab(Try and success), Kaggle (fail: Idk)
- Inject to Finance Tracker project?? (Through Rest API)

### TODO
- [x] Survey
- [ ] Search Engine
- [ ] DB Operation
- [ ] Retrieval relevant document
- [ ] Save relevant document
- [ ] Embedding
- [ ] RAG
- [ ] Finalize answer
- [ ] Metric

### Further work
- May I create another agent to critical thinking?
- Create loop to ensure accuracy
- What 