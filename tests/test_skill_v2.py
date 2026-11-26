import random
import pytest
from backend import skill_engine as s

def test_seeded_routing():
    cases=[("P0456 diagnostic", "automotive-dtc"),("employee leave","hr-policy"),("postgres health","database-health"),("hybrid search","retrieval-inspector")]
    random.Random(42).shuffle(cases)
    for q, expected in cases:
        assert s.route(q)==expected

def test_unknown():
    with pytest.raises(ValueError): s.route("hello")

def test_dynamic_instructions():
    assert "human review" in s.instructions("automotive-dtc").lower()
