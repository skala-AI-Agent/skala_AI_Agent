# FILE: agent3.py
# (Agent 3: Market Assessment RAG)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers.json import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.schema.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

# 공유 자원 및 상태 import
from graph_state import GraphState
from config import llm_mini, simple_web_search, rag_embeddings  # 수정

def run_agent_3_market_rag(state: GraphState) -> GraphState:
    """Agent 3: Performs market assessment using RAG."""
    
    # Chroma 텔레메트리 완전 비활성화
    import chromadb.config
    chromadb.config.Settings(anonymized_telemetry=False)
    
    startup_name = state["current_startup_data"]["name"]
    segment = state["current_startup_data"]["sector"]
    print(f"--- (3) EXECUTING AGENT 3: MARKET RAG for {startup_name} ---")

    # 1. 웹 검색 (RAG 문서 수집)
    search_query = f"{startup_name} {segment} market size TAM SAM SOM CAGR"
    search_results = simple_web_search(search_query, max_results=5)  # 수정
    
    documents = [Document(page_content=res.get("content", ""), metadata={"source": res.get("url", "")}) 
                 for res in search_results if res.get("content")]
    
    if not documents:
        print("--- (3) RAG: 웹 검색 결과가 없습니다. ---")
        return {**state, "market_assessment_output": {"error": "No market data found."}}


    # 2. Split
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)

    # 3. Embed & Store (all-mpnet-base-v2 사용)
    try:
        vectorstore = Chroma.from_documents(documents=splits, embedding=rag_embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    except Exception as e:
        print(f"--- (3) RAG 벡터스토어 생성 실패: {e} ---")
        return {**state, "market_assessment_output": {"error": f"Vectorstore creation failed: {e}"}}

    # 4. RAG Chain
    rag_prompt = ChatPromptTemplate.from_template("""
Based on context, analyze the market for '{startup_name}'. Return JSON only.
Context: {context}
Analyze:
1. tam_sam_som: Estimated TAM, SAM, and SOM.
2. cagr: Estimated CAGR for this market.
3. target_audience: Primary target audience.
{{ "tam_sam_som": "...", "cagr": "...", "target_audience": "..." }}
    """)
    
    rag_chain = (
        {"context": retriever | (lambda docs: "\n\n".join(d.page_content for d in docs)), 
         "startup_name": (lambda x: startup_name)}
        | rag_prompt | llm_mini | JsonOutputParser()
    )
    
    try:
        output = rag_chain.invoke(startup_name)
    except Exception as e:
        print(f"--- (3) RAG Chain Error: {e} ---")
        output = {"error": str(e)}
        
    vectorstore.delete_collection() # 임시 벡터스토어 정리
    return {**state, "market_assessment_output": output}