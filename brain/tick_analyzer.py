import sqlite3
import json
import argparse
from pathlib import Path

def analyze_tick_db(db_path):
    """Parses Tsukuyomi experiment_history.db and recreates high-level narrative."""
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get Dialogue
    dialogue_path = Path(db_path).parent / "dialogue" / "transcript.jsonl"
    dialogue_entries = []
    if dialogue_path.exists():
        with open(dialogue_path, 'r') as f:
            for line in f:
                dialogue_entries.append(json.loads(line))

    print(f"--- Tsukuyomi Simulation Narrative: {db_path.parent.name} ---")

    report = []
    report.append(f"# Tsukuyomi Simulation Report: {db_path.parent.name}")

    # 1. Timeline Reconstruction
    cursor.execute("SELECT MIN(tick_number), MAX(tick_number) FROM ticks")
    start_tick, end_tick = cursor.fetchone()
    report.append(f"**Time Horizon:** {start_tick} -> {end_tick} Ticks (approx {(end_tick-start_tick)/20:.1f}s)")

    # Group Dialogue by Tick Ranges for better flow
    timeline = sorted(dialogue_entries, key=lambda x: x['tick'])

    report.append("\n## Narrative Timeline")
    print("\n--- Narrative Timeline ---")
    for entry in timeline:
        tick = entry['tick']
        who = entry['who']
        msg = entry['message']
        line = f"[T:{tick:05}] **{who}**: {msg}"
        report.append(line)
        print(f"[T:{tick:05}] {who:15} | {msg[:100]}{'...' if len(msg) > 100 else ''}")

    # 2. Key Action Analysis (Search resolutions)
    cursor.execute("SELECT tick_number, tick_state_json FROM ticks")
    agents = set()
    initial_pad = {}
    final_pad = {}
    
    for tick, state_json in cursor.fetchall():
        data = json.loads(state_json)
        actors = data.get("world_state", {}).get("actors", {})
        for aid, adata in actors.items():
            agents.add(aid)
            pad = adata.get("emotional_state", {})
            if aid not in initial_pad: initial_pad[aid] = pad
            final_pad[aid] = pad

    report.append("\n## Cast of Characters")
    print("\n--- Cast of Characters ---")
    for agent_id in sorted(list(agents)):
        report.append(f"- {agent_id}")
        print(f"- {agent_id}")

    report.append("\n## Emotional Arc Summary")
    print("\n--- Emotional Arc Summary ---")
    for agent_id in sorted(list(agents)):
        i = initial_pad.get(agent_id, {})
        f = final_pad.get(agent_id, {})
        report.append(f"- **{agent_id}** | P:{i.get('pleasure',0):.1f} -> {f.get('pleasure',0):.1f} | A:{i.get('arousal',0):.1f} -> {f.get('arousal',0):.1f}")
        print(f"{agent_id:15} | P:{i.get('pleasure',0):.1f} -> {f.get('pleasure',0):.1f} | A:{i.get('arousal',0):.1f} -> {f.get('arousal',0):.1f}")

    # Save report
    report_path = db_path.parent / f"simulation_report_{db_path.parent.name}.md"
    with open(report_path, 'w') as f:
        f.write("\n".join(report))
    print(f"\nReport saved to: {report_path}")

    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("db", type=Path)
    args = parser.parse_args()
    analyze_tick_db(args.db)
