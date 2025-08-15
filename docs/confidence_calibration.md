# Confidence Calibration & Learning (Phase 16)

OriginFlow’s governance and safety policies define static confidence
thresholds for auto‑approving actions based on risk class.  To make
these thresholds adaptive and responsive to real‑world usage, the
system now introduces a **Confidence Calibrator**.

## ConfidenceCalibrator

The calibrator records user feedback (approval or rejection) for each
action produced by an agent and adjusts subsequent confidence scores
accordingly.  The calibration strategy implemented in
`backend/utils/confidence_calibration.py` works as follows:

1. **Feedback records**: Every time a user approves or rejects an
   action, the calibrator’s `record_feedback` method is called with
   the agent name, action type, original confidence and a boolean flag
   indicating approval.  These records are grouped by
   `(agent_name, action_type)`.
2. **Acceptance rate**: For each group, an acceptance rate is computed
   as the fraction of approved actions.  If no feedback exists,
   a neutral rate of 0.5 is assumed.
3. **Confidence calibration**: The calibrator blends the original
   confidence with the neutral value 0.5 according to the acceptance
   rate.  Fully accepted actions retain their original confidence,
   while rejected ones drift towards 0.5, making auto‑approval less
   likely.
4. **Dynamic thresholds**: The base auto‑approval threshold defined by
   governance is adjusted up or down using the acceptance rate.  High
   acceptance lowers the threshold slightly, while low acceptance
   raises it.  Thresholds are clamped between 0.5 and 0.95.

## Integration

In a full OriginFlow deployment, the orchestrators would invoke
`ConfidenceCalibrator.calibrate_confidence` when assigning
confidence scores to actions and use `get_threshold` to determine
whether an action should be auto‑approved.  They would also call
`record_feedback` whenever a user explicitly approves or rejects an
action in the UI.

Although the minimal codebase here does not include complete
orchestrators, the calibrator can be integrated easily by
wrapping confidence assignments and auto‑approval decisions around
these methods.  This adaptive approach helps the system align its
confidence assessments with user expectations over time.

## Developer Guidance

Developers looking to integrate the calibrator into new agents or
orchestrators should consult the [developer onboarding guide](developer_guide.md).
The guide outlines how to use the `ConfidenceCalibrator` when assigning
confidence scores, update governance thresholds based on acceptance rates and
record user feedback to improve calibration over time.
