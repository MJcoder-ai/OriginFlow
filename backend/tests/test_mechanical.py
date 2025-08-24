from backend.tools.mechanical import (
    layout_racking,
    attachment_spacing,
    LayoutRackingInput,
    AttachmentSpacingInput,
    RoofPlane,
    RailSpec,
)


def test_layout_racking_generates_rails_and_attachments():
    roof = RoofPlane(
        id="R1",
        tilt_deg=25,
        azimuth_deg=180,
        width_m=10.0,
        height_m=6.0,
        setback_m=0.5,
    )
    inp = LayoutRackingInput(
        session_id="s", request_id="r", roof=roof, modules_count=14
    )
    patch = layout_racking(inp)
    metas = [op for op in patch.operations if op.op == "set_meta"]
    assert metas and metas[0].value["path"] == "mechanical"
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    assert "rails" in ann.value["attrs"]["summary"]


def test_attachment_spacing_warns_when_exceeded():
    ai = AttachmentSpacingInput(
        session_id="s",
        request_id="r2",
        span_request_m=2.0,
        rail_spec=RailSpec(allowable_span_m=1.5),
    )
    patch = attachment_spacing(ai)
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    res = ann.value["attrs"]["result"]["findings"]
    assert any(f["code"] == "SPAN_EXCEEDED" for f in res)


def test_attachment_spacing_ok_within_span():
    ai = AttachmentSpacingInput(
        session_id="s",
        request_id="r3",
        span_request_m=1.0,
        rail_spec=RailSpec(allowable_span_m=1.5),
    )
    patch = attachment_spacing(ai)
    ann = [op for op in patch.operations if op.op == "add_edge"][0]
    res = ann.value["attrs"]["result"]["findings"]
    assert res == []
    assert ann.value["attrs"]["span_ok"] is True

