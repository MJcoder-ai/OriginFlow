from backend.services.odl_parser import parse_odl_text


def test_parse_basic_odl():
    txt = """
    # Layer: single_line
    panel P1 at(layer="single_line", x=220, y=140)
    inverter I1 at(layer="single_line", x=420, y=140)
    link P1 -> I1 route[(220,140) -> (420,140)]
    """
    snap = parse_odl_text(txt)
    ids = {c.id for c in snap.components}
    assert "P1" in ids and "I1" in ids
    assert snap.links and snap.links[0].source_id == "P1"

