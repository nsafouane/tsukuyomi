"""
Catalyst System - Narrative Event Injection

Handles the creation and injection of 'Catalyst' events to drive the narrative
and maintain simulation tension.
"""

import logging
import random
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger("CatalystSystem")


@dataclass
class CatalystTemplate:
    id: str
    name: str
    description: str
    tags: List[str]
    parameters: Dict[str, str]


class CatalystSystem:
    """
    Manages narrative triggers called 'Catalysts'.
    """

    def __init__(self, fate_engine):
        self.fate_engine = fate_engine
        self.templates = {
            "leaked_evidence": CatalystTemplate(
                id="leaked_evidence",
                name="Leaked Evidence",
                description="Confidential documents about the trial have been found.",
                tags=["evidence", "mystery", "trial"],
                parameters={"doc_type": "court records", "severity": "high"},
            ),
            "witness_outburst": CatalystTemplate(
                id="witness_outburst",
                name="Witness Outburst",
                description="A key witness has interrupted proceedings with emotional testimony.",
                tags=["social", "trial", "emotion"],
                parameters={
                    "witness_name": "defendant",
                    "interruption_type": "emotional",
                },
            ),
            "anonymous_tip": CatalystTemplate(
                id="anonymous_tip",
                name="Anonymous Tip",
                description="An anonymous source has contacted the court with new information.",
                tags=["mystery", "trial", "evidence"],
                parameters={"tip_type": "informer", "content": "new_evidence"},
            ),
            "social_media_trend": CatalystTemplate(
                id="social_media_trend",
                name="Social Media Trend",
                description="A trending topic on social media is affecting public perception of the case.",
                tags=["social", "trial", "media"],
                parameters={"platform": "twitter", "hashtag": "case_name"},
            ),
            "jury_conflict": CatalystTemplate(
                id="jury_conflict",
                name="Jury Conflict",
                description="Two jurors have a heated disagreement about the case.",
                tags=["social", "conflict", "trial"],
                parameters={
                    "juror_a": "juror_1",
                    "juror_b": "juror_2",
                    "topic": "evidence",
                },
            ),
            "time_pressure": CatalystTemplate(
                id="time_pressure",
                name="Time Pressure",
                description="The judge announces a deadline for the jury to reach a verdict.",
                tags=["trial", "emotion", "urgency"],
                parameters={"deadline": "end_of_day", "consequence": "mistrial"},
            ),
            "new_testimony": CatalystTemplate(
                id="new_testimony",
                name="New Testimony",
                description="A previously unavailable witness suddenly becomes available.",
                tags=["mystery", "trial", "evidence"],
                parameters={
                    "witness_name": "surprise_witness",
                    "testimony_type": "alibi",
                },
            ),
            "media_pressure": CatalystTemplate(
                id="media_pressure",
                name="Media Pressure",
                description="Reporters gather outside the courthouse, increasing public scrutiny.",
                tags=["social", "trial", "emotion"],
                parameters={"media_type": "press", "intensity": "high"},
            ),
        }

    def trigger_random_catalyst(self, tick: int) -> str:
        """Pick a template and trigger it."""
        template_id = random.choice(list(self.templates.keys()))
        return self.trigger_catalyst(template_id, tick)

    def trigger_catalyst(self, template_id: str, tick: int) -> str:
        """Inject a catalyst event into the FateEngine's global events list."""
        if template_id not in self.templates:
            logger.error(f"Catalyst template {template_id} not found.")
            return ""

        template = self.templates[template_id]
        event_id = str(uuid.uuid4())

        # Format: TYPE|NAME|ID|TICK|DESCRIPTION|JSON_PARAMS
        params_json = random.choice(
            [json_data for json_data in [template.parameters]]
        )  # simplify
        import json

        event_str = f"CATALYST|{template.name}|{event_id}|{tick}|{template.description}|{json.dumps(template.parameters)}"

        # Inject into FateEngine
        if hasattr(self.fate_engine, "add_global_event"):
            self.fate_engine.add_global_event(event_str)
        else:
            # Direct access if no helper method (fallback)
            self.fate_engine.world_state.global_events.append(event_str)
            # Maintain a reasonable size
            if len(self.fate_engine.world_state.global_events) > 50:
                self.fate_engine.world_state.global_events.pop(0)

        logger.info(
            f"🎭 Catalyst Triggered: {template.name} ({event_id}) at tick {tick}"
        )
        return event_str
