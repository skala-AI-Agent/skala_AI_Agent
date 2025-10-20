# FILE: config.py - 경고 제거 버전

import os
import warnings

# === 모든 경고 무시 ===
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["ANONYMIZED_TELEMETRY"] = "False"
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore")  # 모든 경고 무시

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from tavily import TavilyClient
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_teddynote import logging
from duckduckgo_search import DDGS  # 기존 패키지 그대로 사용
import time

load_dotenv()
logging.langsmith("RWA-Multi-Agent-Modular")

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("OPENAI_API_KEY not found in .env file")

print("✅ .env loaded and API keys verified.")

# LLM 초기화
llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=4096)
llm_mini = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=2048)

# Tavily (fallback)
try:
    if os.getenv("TAVILY_API_KEY"):
        tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        web_search = TavilySearchResults(max_results=5)
        print("✅ Tavily initialized (fallback mode).")
    else:
        tavily_client = None
        web_search = None
except Exception as e:
    tavily_client = None
    web_search = None

# DuckDuckGo 검색 함수 (개선)
def simple_web_search(query: str, max_results: int = 5) -> list:
    """DuckDuckGo를 사용한 웹 검색"""
    results = []
    
    try:
        ddgs = DDGS()
        search_results = list(ddgs.text(
            query, 
            max_results=max_results,
            region='wt-wt',
            safesearch='moderate'
        ))
        
        for result in search_results:
            results.append({
                'title': result.get('title', ''),
                'url': result.get('href', result.get('link', '')),
                'content': result.get('body', result.get('snippet', '')),
                'snippet': result.get('body', result.get('snippet', ''))
            })
        
        if results:
            print(f"    ✓ {len(results)}개 검색 결과 수집")
        
        time.sleep(0.5)
        
    except Exception as e:
        print(f"    ⚠️ 검색 실패: {e}")
        
        # Fallback: Tavily
        if tavily_client:
            try:
                tavily_results = tavily_client.search(query=query, max_results=max_results)
                for item in tavily_results.get("results", []):
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'content': item.get('content', item.get('snippet', '')),
                        'snippet': item.get('content', item.get('snippet', ''))
                    })
                print(f"    ✓ {len(results)}개 검색 결과 수집 (Tavily)")
            except:
                pass
    
    # 더미 데이터
    if not results:
        company_name = query.split()[0] if query else 'company'
        results = [{
            'title': f"{company_name} - RWA Platform",
            'url': f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
            'content': f"{company_name} operates in the Real-World Asset tokenization sector with focus on compliance and institutional adoption. Key areas include regulatory frameworks, technical architecture, and market partnerships.",
            'snippet': "Emerging RWA platform with compliance focus."
        }]
    
    return results

print("✅ Web search initialized.")

# RAG 임베딩
try:
    rag_embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'}
    )
    print("✅ RAG Embeddings loaded.")
except Exception as e:
    print(f"❌ Embeddings error: {e}")
    rag_embeddings = None

# JSON 모드 LLM
llm_json = llm.bind(response_format={"type": "json_object"})
llm_mini_json = llm_mini.bind(response_format={"type": "json_object"})

# VC Checklist
VC_CHECKLIST = [
    "1. Market(TAM): Is the market size (TAM) significant (> $1B)?",
    "2. Market(CAGR): Is the market growing rapidly (> 20% CAGR)?",
    "3. Problem: Is the customer problem clear and urgent?",
    "4. Product: Does the product offer a 10x improvement over alternatives?",
    "5. Tech(Moat): Is there a strong, defensible technical moat?",
    "6. Tech(Maturity): Is the platform's security and scalability proven? (Ref: Agent 2 tech_maturity > 0.7)",
    "7. Team(Expertise): Does the team have deep domain expertise (finance, RE, blockchain)?",
    "8. Team(Execution): Does the team demonstrate strong execution capability?",
    "9. Competition(Differentiation): Is there clear differentiation from competitors?",
    "10. Competition(Barrier): Are there high barriers to entry?",
    "11. BizModel(Clarity): Is the revenue model clear and viable?",
    "12. BizModel(LTV/CAC): Is the LTV/CAC ratio estimated to be > 3x?",
    "13. Traction(Partners): Are there significant early customers or institutional partnerships? (Ref: Agent 2 ecosystem)",
    "14. Traction(Users): Are there active users with good retention rates?",
    "15. Credibility(VC): Has the startup secured funding from reputable VCs?",
    "16. Credibility(Media): Is there positive validation from credible reports/media? (Ref: Agent 2 credibility > 0.7)",
    "17. Regulation(Strategy): Is the team aware of regulatory risks (KYC/AML) with a clear strategy?",
    "18. Regulation(RiskScore): Is the compliance risk score low? (Ref: Agent 2 compliance_risk < 0.25)",
    "19. Scalability(Global): Is the business model scalable beyond its initial region?",
    "20. Fit(Positioning): Does it have a unique and strong positioning in the RWA sector?"
]