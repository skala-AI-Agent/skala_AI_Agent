# FILE: graph_state.py
# (공유 GraphState 정의)

from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict):
    """
    Represents the global state of the investment evaluation graph.
    
    Attributes:
        investor_persona (str): The persona type ('aggressive' or 'conservative').
        persona_rationale (str): The reasoning for the persona selection.
        evaluation_results (List[Dict]): The full, ranked list of startups from Agent 1.
        current_startup_index (int): The index of the startup currently being evaluated.
        current_startup_data (Dict): The full data blob for the current startup.
        
        tech_summary_output (Optional[Dict]): Output from Agent 2.
        market_assessment_output (Optional[Dict]): Output from Agent 3.
        competitor_analysis_output (Optional[Dict]): Output from Agent 4.
        investment_decision_output (Optional[Dict]): Output from Agent 5.
        
        decision_log (List[str]): A log of decisions made (e.g., ["보류", "부정적"]).
        final_report (Optional[str]): The final Markdown report.
    """
    # From Agent 0
    investor_persona: str
    persona_rationale: str
    
    # From Agent 1
    evaluation_results: List[Dict] 
    current_startup_index: int
    current_startup_data: Dict
    
    # Agent Outputs
    tech_summary_output: Optional[Dict]
    market_assessment_output: Optional[Dict]
    competitor_analysis_output: Optional[Dict]
    investment_decision_output: Optional[Dict]
    
    # Control Flow
    decision_log: List[str]
    
    # Final Output
    final_report: Optional[str]