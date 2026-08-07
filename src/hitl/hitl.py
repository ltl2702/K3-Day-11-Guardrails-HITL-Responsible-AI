"""
Lab 11 — Part 4: Human-in-the-Loop Design
  TODO 11: Confidence Router
  TODO 12: Design 3 HITL decision points
"""
from dataclasses import dataclass


# ============================================================
# TODO 11: Implement ConfidenceRouter
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "change_beneficiary",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if action_type in HIGH_RISK_ACTIONS:
            return RoutingDecision(
                action="escalate",
                confidence=confidence,
                reason=f"High-risk action: {action_type}",
                priority="high",
                requires_human=True,
            )

        if confidence >= self.HIGH_THRESHOLD:
            return RoutingDecision(
                action="auto_send",
                confidence=confidence,
                reason="High confidence",
                priority="low",
                requires_human=False,
            )

        if confidence >= self.MEDIUM_THRESHOLD:
            return RoutingDecision(
                action="queue_review",
                confidence=confidence,
                reason="Medium confidence — needs review",
                priority="normal",
                requires_human=True,
            )

        return RoutingDecision(
            action="escalate",
            confidence=confidence,
            reason="Low confidence — escalating",
            priority="high",
            requires_human=True,
        )


# ============================================================
# TODO 12: Design 3 HITL decision points + a review lifecycle
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
# - approval_path: What approve/reject/timeout decision is recorded?
# - audit_fields: Which correlation ID, intent and proposed action/diff are logged?
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "Transfer or beneficiary change approval",
        "trigger": (
            "A transfer_money or change_beneficiary action is proposed, "
            "regardless of model confidence."
        ),
        "hitl_model": "human-in-the-loop",
        "context_needed": (
            "Old and new beneficiary, amount, currency, source account, "
            "device/IP, recent account activity and anomaly indicators."
        ),
        "example": (
            "The agent proposes changing the beneficiary and transferring "
            "50,000,000 VND from a newly observed device."
        ),
        "approval_path": (
            "Approve records reviewer identity and releases the exact proposal; "
            "reject cancels it; timeout places it on hold and never transfers funds."
        ),
        "audit_fields": (
            "request_id, layer=hitl, intent, old_value, new_value, amount, "
            "risk_signals, reviewer_id, reviewer_decision, decision_timestamp"
        ),
    },
    {
        "id": 2,
        "name": "Account closure approval",
        "trigger": (
            "The agent proposes close_account or delete_data, including when "
            "the customer message claims urgency or executive authority."
        ),
        "hitl_model": "human-in-the-loop",
        "context_needed": (
            "Verified customer identity, account status, remaining balance, "
            "pending payments, linked products and the proposed closure scope."
        ),
        "example": (
            "A message asks to close an account immediately while a loan "
            "repayment and two card settlements remain pending."
        ),
        "approval_path": (
            "Approve schedules closure after prerequisites; reject keeps the "
            "account open; timeout rejects the action and alerts operations."
        ),
        "audit_fields": (
            "request_id, layer=hitl, intent, account_state, dependencies, "
            "proposed_action, reviewer_id, reviewer_decision, timeout_status"
        ),
    },
    {
        "id": 3,
        "name": "Credential or personal-data update",
        "trigger": (
            "A change_password or update_personal_info action is proposed, "
            "or identity/risk signals disagree."
        ),
        "hitl_model": "human-as-tiebreaker",
        "context_needed": (
            "Authentication factors, old/new field diff, device history, "
            "fraud score and any recent recovery attempts."
        ),
        "example": (
            "A request from a new device changes both the phone number and "
            "password after failed authentication attempts."
        ),
        "approval_path": (
            "Approve applies only the displayed diff; reject preserves old "
            "values; timeout holds the request and sends a fraud-review alert."
        ),
        "audit_fields": (
            "request_id, layer=hitl, intent, masked_old_value, masked_new_value, "
            "risk_score, reviewer_id, reviewer_decision, decision_timestamp"
        ),
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
