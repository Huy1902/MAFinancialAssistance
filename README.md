## This is my Multi Agent Financial Assitance

## My check list

### Survey

- Agent: What is?
- Search Engine: DuckDuckGo
- RAG
- Memory: Document, DB handling
- Basic pipeline:
  - Reasoning though (Planing) - Use prompt
  - Action: use tool: search engine + RAG
  - Searching:
  - Retrieval relevant document (Need a measure)
  - Embedding document (Some emb from hugging face)
  - Save to database (memory)
    - Clear temp file (if needed)
- Retrieval from RAG (search + user document)
  - User document may need PDF reader and Image reader?? (Some tool in Python PyPDF)
- Prompt conversation: {role} {context}?? ()
- Streamlit on Colab(Try and success), Kaggle (fail: Idk), Flask for simple(I try this first)
- Inject to Finance Tracker project?? (Through Rest API)

- Langchain support a good tool (Why don't I use it sooner????:((( )
### TODO

- [x] Survey
- [x] Agent Template
  - [x] Prompt for COT
  - [x] Conclusion and evaluation
- [x] scrap tool
  - [x] Scrap link
  - [x] Just download file
- [x] Execute code tool (no test now 🤡 )
  - [x] Install package
  - [x] sys execute
- [x] Search Engine (Quite simple)
- [x] DB Operation
- [x] Re try and fail sql query handler (Use graph and tool from langchain)
- [ ] Retrieval relevant document
- [ ] Save relevant document
- [ ] Embedding
- [x] RAG
- [ ] Finalize answer
- [ ] Metric

### Further work

- May I create another agent to critical thinking?
- Create loop to ensure accuracy
