# FILE: agent2.py
# (Agent 2: Technical Due Diligence Sub-Graph) - build_agent2_graph 더미 노드 수정됨

import json
import uuid
from typing import TypedDict, List, Dict, Any, Literal
from typing_extensions import NotRequired
from datetime import datetime
from urllib.parse import urlparse
from langgraph.graph import StateGraph, START, END

# config에서 llm, llm_mini, tavily_client, llm_json import
from config import llm, llm_mini, tavily_client, llm_json

# --- Agent 2의 독립적인 상태 정의 ---
class Agent2Company(TypedDict, total=False): name: str; website: str; segment: str; region: str; funding_stage: str
class Agent2Evidence(TypedDict, total=False): id: str; source: str; url: str; date: str; snippet: str; relates_to: str
class Agent2Scores(TypedDict, total=False): domain_fit: float; tech_maturity: float; credibility: float; compliance_risk: float; ecosystem: float
class Agent2OutputPayload(TypedDict, total=False): name: str; website: str; segment: str; region: str; funding_stage: str; scores: Agent2Scores; final_score: float; reason: str; evidence: List[Agent2Evidence]; notes: Dict[str, Any]; narrative: str
class Agent2State(TypedDict, total=False):
    """Internal state for the Agent 2 sub-graph."""
    startup_json: Dict[str, Any]; company: Agent2Company; raw_signals: List[Dict[str, Any]]
    normalized_signals: List[Dict[str, Any]]; scores: Agent2Scores; final_score: float
    evidence: List[Agent2Evidence]; decision_notes: Dict[str, Any]; final_narrative: str
    output_payload: Agent2OutputPayload; logs: NotRequired[List[str]]

# --- Agent 2 유틸리티 함수 ---
# (유틸리티 함수는 이전과 동일 - 생략)
def _agent2_clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float: return max(lo, min(hi, x))
def _agent2_today_iso() -> str: return datetime.utcnow().date().isoformat()
def _agent2_domain_naive(host_or_url: str) -> str:
    if not host_or_url: return ""
    host = host_or_url
    if "://" in host_or_url:
        try: host = urlparse(host_or_url).hostname or ""
        except Exception: host = ""
    if not host: return ""
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host
def _agent2_source_type(url: str, company_site: str) -> str:
    d = _agent2_domain_naive(url); c = _agent2_domain_naive(company_site)
    if c and d == c: return "site"
    if d in {"github.com", "gitlab.com"}: return "repo"
    if d in {"deloitte.com", "mckinsey.com", "bcg.com", "pwc.com", "kpmg.com"}: return "report"
    if d in {"reuters.com", "bloomberg.com", "coindesk.com", "techcrunch.com", "forbes.com"}: return "press"
    return "other"
def _agent2_parse_date(s: str | None) -> str:
    if not s: return _agent2_today_iso()
    try: return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except Exception: return _agent2_today_iso()
def _agent2_log(state: Agent2State, msg: str) -> None:
    if "logs" not in state or state["logs"] is None: state["logs"] = []
    state["logs"].append(msg)
    print(f"   [Agent 2 Log] {msg}")


# --- Agent 2 노드 함수들 ---
# (노드 함수들은 이전 답변과 동일 - 변경 없음)
def agent2_ingest_input(state: Agent2State) -> Agent2State:
    sj = state.get("startup_json", {})
    state["company"] = { "name": sj.get("name", ""), "website": sj.get("website", ""), "segment": sj.get("segment", ""), "region": sj.get("region", ""), "funding_stage": sj.get("funding_stage", ""), }
    _agent2_log(state, "입력 데이터 처리 완료.")
    return state

def agent2_collect_signals(state: Agent2State) -> Agent2State:
    from config import simple_web_search  # 추가
    
    company = state["company"]
    queries = [
        f'{company.get("name","")} {company.get("segment","")}',
        f'{company.get("name","")} tokenization KYC AML licensing'
    ]
    out: List[Dict[str, Any]] = []
    
    for q in queries:
        try:
            # simple_web_search 사용
            results = simple_web_search(q, max_results=5)
            for item in results:
                out.append({
                    "source": _agent2_source_type(item.get("url", ""), company.get("website", "")),
                    "url": item.get("url", ""),
                    "date": _agent2_today_iso(),
                    "snippet": item.get("content", "")[:600],
                })
        except Exception as e:
            _agent2_log(state, f"검색 오류: {e}")
    
    dedup = list({(s["source"], s["url"]): s for s in out}.values())
    state["raw_signals"] = dedup
    _agent2_log(state, f"{len(dedup)}개 신호 수집 완료.")
    return state

def agent2_normalize_enrich(state: Agent2State) -> Agent2State:
    out = []
    for s in state.get("raw_signals", []):
        src = s.get("source", "other")
        cred = 0.85 if src in {"report", "site"} else (0.7 if src == "press" else 0.6)
        out.append({ "source": src, "url": s.get("url", ""), "date": s.get("date", ""), "snippet": s.get("snippet", ""), "credibility": cred })
    state["normalized_signals"] = out
    _agent2_log(state, f"{len(out)}개 신호 정규화 완료.")
    return state

def agent2_guard_quick_check(state: Agent2State) -> Literal["resample", "ok"]:
    signals = state.get("normalized_signals", [])
    if not signals:
        _agent2_log(state, "guard_quick_check: 수집된 신호가 없음. 재수집 시도.")
        return "resample"
    _agent2_log(state, f"guard_quick_check: {len(signals)}개 신호 발견. 분석 진행.")
    return "ok"

def agent2_score_by_rules(state: Agent2State) -> Agent2State:
    company = state["company"]; signals = state.get("normalized_signals", [])
    has_kyc = any("kyc" in s.get("snippet", "").lower() or "aml" in s.get("snippet", "").lower() for s in signals)
    has_report = any(s.get("source") == "report" for s in signals)
    has_partnership = any("partnership" in s.get("snippet", "").lower() for s in signals)
    base_scores: Agent2Scores = { "domain_fit": _agent2_clamp(0.82 if "token" in company.get("segment", "").lower() else 0.65), "tech_maturity": _agent2_clamp(0.74 if has_kyc else 0.62), "credibility": _agent2_clamp(0.73 if has_report else 0.6), "compliance_risk": _agent2_clamp(0.18 if has_kyc else 0.32), "ecosystem": _agent2_clamp(0.78 if has_partnership else 0.62), }
    brief = "\n".join([f"- [{s.get('source')}] {s.get('snippet')}" for s in signals][:8])
    prompt = f"Adjust RWA tech scores [0,1] with small corrections. Return JSON only.\nSignals:\n{brief}\nBase:\n{json.dumps(base_scores)}"
    try:
        resp = llm_json.invoke(prompt); delta = json.loads(resp.content)
        fused = {k: _agent2_clamp(base_scores[k] + max(-0.05, min(0.05, float(delta.get(k, v)) - base_scores[k]))) for k, v in base_scores.items()}
        state["scores"] = fused; _agent2_log(state, "규칙 기반 점수 + LLM 보정 완료.")
    except Exception as e:
        state["scores"] = base_scores; _agent2_log(state, f"LLM 보정 실패, 기본 점수 사용. 오류: {e}")
    return state

def agent2_calculate_final(state: Agent2State) -> Agent2State:
    s = state["scores"]
    final = 0.30*s["domain_fit"] + 0.25*s["tech_maturity"] + 0.25*s["credibility"] + 0.10*s["ecosystem"] - 0.20*s["compliance_risk"]
    state["final_score"] = _agent2_clamp(final); _agent2_log(state, f"최종 점수 계산 완료: {final:.3f}.");
    return state

def agent2_build_evidence(state: Agent2State) -> Agent2State:
    signals = state.get("normalized_signals", [])
    if not signals: _agent2_log(state, "증거 생성: 신호 없음."); state["evidence"] = []; return state
    top = sorted(signals, key=lambda s: s.get("credibility", 0), reverse=True)[:8]
    bullets = "\n".join([f"- ({s.get('source')}) {s.get('snippet')} | {s.get('url')}" for s in top])
    prompt = f"Summarize 1–2 short evidence items per score dimension (domain_fit, tech_maturity, credibility, compliance_risk, ecosystem) from signals. Return JSON arrays, each item has 'snippet','url','source'.\nSignals:\n{bullets}"
    try:
        resp = llm_json.invoke(prompt); bundle = json.loads(resp.content)
        ev: List[Agent2Evidence] = []
        for k, items in bundle.items():
            if not isinstance(items, list): continue
            for it in items[:2]:
                if not isinstance(it, dict): continue
                ev.append({ "id": f"ev_{uuid.uuid4().hex[:8]}", "source": it.get("source", "other"), "url": it.get("url", ""), "date": _agent2_today_iso(), "snippet": it.get("snippet", ""), "relates_to": str(k), })
        if not ev and top: _agent2_log(state, "LLM이 빈 증거를 반환. 폴백 증거 사용."); ev = [{"id": f"ev_{uuid.uuid4().hex[:8]}", "source": s.get("source", "other"), "url": s.get("url", ""), "date": s.get("date", _agent2_today_iso()), "snippet": s.get("snippet", ""), "relates_to": "credibility"} for s in top[:3]]
        state["evidence"] = ev; _agent2_log(state, f"{len(ev)}개 증거 생성 완료.")
    except Exception as e:
        fallback = [{"id": f"ev_{uuid.uuid4().hex[:8]}", "source": s.get("source", "other"), "url": s.get("url", ""), "date": s.get("date", _agent2_today_iso()), "snippet": s.get("snippet", ""), "relates_to": "credibility"} for s in top[:3]]
        state["evidence"] = fallback; _agent2_log(state, f"LLM 증거 생성 실패, {len(fallback)}개 폴백 증거 사용. 오류: {e}")
    return state

def agent2_decision_notes(state: Agent2State) -> Agent2State:
    s = state["scores"]
    strengths = [item for item in [ "High domain fit." if s["domain_fit"] >= 0.75 else None, "Mature tech." if s["tech_maturity"] >= 0.70 else None, "Solid partners." if s["ecosystem"] >= 0.70 else None ] if item]
    risks = [item for item in [ "Regulatory risk." if s["compliance_risk"] >= 0.25 else None, "Needs more credibility proof." if s["credibility"] < 0.65 else None ] if item]
    prompt = f"Write one positioning sentence. Be neutral.\nscores={json.dumps(s)}\nstrengths={strengths}\nrisks={risks}"
    try:
        sent = llm_mini.invoke(prompt).content.strip()
    except Exception as e: _agent2_log(state, f"결정 노트 생성 실패: {e}"); sent = "Potential observed, monitoring required."
    state["decision_notes"] = {"strengths": strengths[:3], "risks": risks[:3], "positioning": sent}; _agent2_log(state, "결정 노트 생성 완료.");
    return state

def agent2_generate_final_narrative(state: Agent2State) -> Agent2State:
    c, s, ev = state["company"], state["scores"], state.get("evidence", [])[:8]
    pos = state.get("decision_notes", {}).get("positioning", "")
    final_score = state.get("final_score", 0.0)
    evidence_block = "\n".join([f"- [{idx+1}] ({e.get('source')}) {e.get('snippet', '')[:100]}... ({e.get('url')})" for idx, e in enumerate(ev)])
    prompt = f"""Write a 350–500 word markdown DD report with exact headers: Overview, Technology & Architecture, Governance & Compliance, Credibility & Ecosystem, Risks & Watchpoints, Bottom Line.
Context: Company: {c.get('name','')}, Segment: {c.get('segment','')}, Scores: {json.dumps(s)}, Final: {final_score:.3f}, Pos: {pos}, Evidence:\n{evidence_block}"""
    try:
        text = llm.invoke(prompt).content.strip()
    except Exception as e: _agent2_log(state, f"최종 내러티브 생성 실패: {e}"); text = "## Overview\nAnalysis failed."
    state["final_narrative"] = text; _agent2_log(state, "최종 내러티브 생성 완료.");
    return state

def agent2_emit_json(state: Agent2State) -> Agent2State:
    c, s = state["company"], state["scores"]
    state["output_payload"] = { "name": c.get("name", ""), "website": c.get("website", ""), "segment": c.get("segment", ""), "region": c.get("region", ""), "funding_stage": c.get("funding_stage", ""), "scores": s, "final_score": float(state["final_score"]), "reason": state.get("decision_notes", {}).get("positioning", ""), "evidence": state.get("evidence", []), "notes": state.get("decision_notes", {}), "narrative": state.get("final_narrative", ""), }
    _agent2_log(state, "최종 출력 페이로드 조립 완료.");
    return state

def agent2_quality_gate(state: Agent2State) -> Literal["fix", "done"]:
    out = state.get("output_payload", {})
    if not out.get("name"): _agent2_log(state, "품질 게이트 실패: 'name' 누락."); return "done"
    if not out.get("narrative"): _agent2_log(state, "품질 게이트 실패: 'narrative' 누락."); return "done"
    evidence = out.get("evidence")
    if evidence is None or len(evidence) == 0: _agent2_log(state, "품질 게이트 실패: 'evidence' 비어있음. 재생성 시도."); return "fix"
    _agent2_log(state, "품질 게이트 통과.");
    return "done"

# --- Agent 2 그래프 빌더 (Export) ---
# agent2.py의 build_agent2_graph() 함수를 다음과 같이 수정:

def build_agent2_graph():
    """
    Builds and compiles the self-contained Agent 2 sub-graph.

    docstring: Builds and compiles the internal LangGraph state machine for Agent 2.
    """
    graph = StateGraph(Agent2State)

    graph.add_node("0_ingest_input", agent2_ingest_input)
    graph.add_node("1_collect_signals", agent2_collect_signals)
    graph.add_node("2_normalize_enrich", agent2_normalize_enrich)
    # 더미 노드 제거 - 조건부 분기는 add_conditional_edges에서만 사용
    graph.add_node("4_score_by_rules", agent2_score_by_rules)
    graph.add_node("5_calculate_final", agent2_calculate_final)
    graph.add_node("6_build_evidence", agent2_build_evidence)
    graph.add_node("7_decision_notes", agent2_decision_notes)
    graph.add_node("7b_generate_final_narrative", agent2_generate_final_narrative)
    graph.add_node("8_emit_json", agent2_emit_json)

    graph.add_edge(START, "0_ingest_input")
    graph.add_edge("0_ingest_input", "1_collect_signals")
    graph.add_edge("1_collect_signals", "2_normalize_enrich")

    # 조건부 엣지: 더미 노드 없이 직접 분기
    graph.add_conditional_edges(
        "2_normalize_enrich",  # 출발 노드
        agent2_guard_quick_check,   # 경로 결정 함수
        {"resample": "1_collect_signals", "ok": "4_score_by_rules"}
    )
    
    graph.add_edge("4_score_by_rules", "5_calculate_final")
    graph.add_edge("5_calculate_final", "6_build_evidence")
    graph.add_edge("6_build_evidence", "7_decision_notes")
    graph.add_edge("7_decision_notes", "7b_generate_final_narrative")
    graph.add_edge("7b_generate_final_narrative", "8_emit_json")

    # 조건부 엣지: 더미 노드 없이 직접 분기
    graph.add_conditional_edges(
        "8_emit_json",   # 출발 노드
        agent2_quality_gate,  # 경로 결정 함수
        {"fix": "6_build_evidence", "done": END}
    )

    return graph.compile()