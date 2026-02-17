"""
Angry Men Experiment - Analysis Module
=====================================

Tools for analyzing experiment results and identifying system gaps.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


class ExperimentAnalyzer:
    """
    Analyzes experiment logs to identify:
    - Conversation patterns
    - Decision reasoning quality
    - Memory effectiveness
    - Belief evolution
    - System performance issues
    """
    
    def __init__(self, logs_dir: Path):
        self.logs_dir = Path(logs_dir)
        self.results = {}
    
    def load_logs(self):
        """Load all log files."""
        # Load narrative summary
        with open(self.logs_dir / "narrative_summary.json") as f:
            self.results["narrative"] = json.load(f)
        
        # Load juror decision logs
        self.results["jurors"] = {}
        for log_file in self.logs_dir.glob("decisions_juror_*.json"):
            juror_id = log_file.stem.replace("decisions_", "")
            with open(log_file) as f:
                self.results["jurors"][juror_id] = json.load(f)
    
    def analyze_narrative_flow(self) -> Dict:
        """Analyze the narrative pacing and flow."""
        narrative = self.results.get("narrative", {})
        
        return {
            "acts_completed": narrative.get("beats_completed", 0),
            "tension_evolution": self._analyze_tension(),
            "emotional_peaks": len(narrative.get("emotional_peaks", [])),
            "conversation_turns": narrative.get("conversation_turns", 0)
        }
    
    def _analyze_tension(self) -> Dict:
        """Analyze tension curve."""
        # Simplified - would need full tension history
        return {"pattern": "unknown", "peaks_detected": 0}
    
    def analyze_decisions(self) -> Dict:
        """Analyze decision quality and reasoning."""
        all_decisions = []
        for juror_id, decisions in self.results.get("jurors", {}).items():
            all_decisions.extend(decisions)
        
        return {
            "total_decisions": len(all_decisions),
            "decision_types": self._count_decision_types(all_decisions),
            "reasoning_coherence": self._assess_reasoning(all_decisions)
        }
    
    def _count_decision_types(self, decisions: List[Dict]) -> Dict:
        """Count decision types."""
        counts = defaultdict(int)
        for d in decisions:
            counts[d.get("decision_type", "unknown")] += 1
        return dict(counts)
    
    def _assess_reasoning(self, decisions: List[Dict]) -> str:
        """Assess reasoning quality."""
        if not decisions:
            return "no_data"
        
        # Check if decisions have reasoning chains
        has_reasoning = sum(1 for d in decisions if "details" in d and d["details"])
        ratio = has_reasoning / len(decisions) if decisions else 0
        
        if ratio > 0.8:
            return "good"
        elif ratio > 0.5:
            return "partial"
        else:
            return "poor"
    
    def analyze_memory_usage(self) -> Dict:
        """Analyze memory system effectiveness."""
        # Would analyze memory retrieval logs
        return {
            "episodic_recall": "unknown",
            "semantic_retrieval": "unknown",
            "memory_gaps": []
        }
    
    def analyze_belief_evolution(self) -> Dict:
        """Analyze how beliefs changed over time."""
        return {
            "beliefs_tracked": 0,
            "significant_changes": 0,
            "stable_beliefs": []
        }
    
    def identify_gaps(self) -> List[Dict]:
        """
        Identify system gaps and weaknesses.
        
        Returns list of gap descriptions with severity and category.
        """
        gaps = []
        
        # Analyze narrative
        narrative = self.analyze_narrative_flow()
        if narrative["acts_completed"] < 4:
            gaps.append({
                "category": "narrative",
                "severity": "high",
                "description": "Not all narrative acts completed",
                "detail": f"Only {narrative['acts_completed']}/4 acts completed"
            })
        
        # Analyze decisions
        decisions = self.analyze_decisions()
        if decisions["reasoning_coherence"] == "poor":
            gaps.append({
                "category": "reasoning",
                "severity": "high",
                "description": "Poor reasoning coherence in decisions",
                "detail": "Decisions lack detailed reasoning chains"
            })
        
        # Analyze memory
        memory = self.analyze_memory_usage()
        if memory["memory_gaps"]:
            gaps.append({
                "category": "memory",
                "severity": "medium",
                "description": "Memory retrieval gaps detected",
                "detail": memory["memory_gaps"]
            })
        
        return gaps
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        report = []
        report.append("=" * 60)
        report.append("EXPERIMENT ANALYSIS REPORT")
        report.append("=" * 60)
        
        # Narrative analysis
        narrative = self.analyze_narrative_flow()
        report.append("\n### NARRATIVE FLOW ###")
        report.append(f"Acts completed: {narrative['acts_completed']}/4")
        report.append(f"Emotional peaks: {narrative['emotional_peaks']}")
        report.append(f"Conversation turns: {narrative['conversation_turns']}")
        
        # Decision analysis
        decisions = self.analyze_decisions()
        report.append("\n### DECISIONS ###")
        report.append(f"Total decisions: {decisions['total_decisions']}")
        report.append(f"Reasoning quality: {decisions['reasoning_coherence']}")
        
        # Gaps
        gaps = self.identify_gaps()
        report.append("\n### IDENTIFIED GAPS ###")
        if gaps:
            for gap in gaps:
                report.append(f"[{gap['severity'].upper()}] {gap['category']}: {gap['description']}")
                report.append(f"  Detail: {gap['detail']}")
        else:
            report.append("No significant gaps identified.")
        
        return "\n".join(report)


def analyze_experiment(logs_dir: str = None):
    """Convenience function to run analysis."""
    if logs_dir is None:
        logs_dir = Path(__file__).parent / "logs"
    
    analyzer = ExperimentAnalyzer(logs_dir)
    analyzer.load_logs()
    
    print(analyzer.generate_report())
    
    return analyzer


if __name__ == "__main__":
    import sys
    
    logs_dir = sys.argv[1] if len(sys.argv) > 1 else None
    analyze_experiment(logs_dir)