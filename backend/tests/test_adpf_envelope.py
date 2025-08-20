from backend.utils.adpf import wrap_response


def test_wrap_response_removes_legacy_top_level_fields():
    env = wrap_response(
        thought="ok",
        card={"title": "hello"},
        patch={"ops": []},
        status="pending",
        warnings=["be careful"],
    )
    assert "card" not in env  # legacy duplication removed
    assert "patch" not in env
    assert env["output"]["card"]["title"] == "hello"
    assert env["output"]["patch"]["ops"] == []
    assert env["status"] == "pending"
    assert env["warnings"] == ["be careful"]

