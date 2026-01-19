
import pytest
from scripts.cam_receipt_diff import calculate_diff

@pytest.fixture
def golden_receipt():
    """Provides a golden receipt for tests."""
    return {
        "metadata": {"source_file": "golden.cad"},
        "anchors": {
            "hole1": {"x": 10, "y": 20, "z": 0},
            "hole2": {"x": 50, "y": 20, "z": 0},
            "center": {"x": 30, "y": 30, "z": 15},
        }
    }

def test_no_regression(golden_receipt):
    """Tests the case where there are no regressions."""
    latest_receipt = golden_receipt.copy()
    diff = calculate_diff(golden_receipt, latest_receipt, 0.25)
    assert not diff["causal_summary"]

def test_anchor_moved_outside_tolerance(golden_receipt):
    """Tests detection of a moved anchor."""
    latest_receipt = golden_receipt.copy()
    latest_receipt["anchors"]["hole1"] = {"x": 10.5, "y": 20, "z": 0} # 0.5mm move
    
    diff = calculate_diff(golden_receipt, latest_receipt, 0.25)
    
    assert "hole1" in diff["causal_summary"]
    assert diff["causal_summary"]["hole1"]["change_type"] == "moved"
    assert diff["causal_summary"]["hole1"]["distance_mm"] == 0.5

def test_anchor_moved_within_tolerance(golden_receipt):
    """Tests that small movements within tolerance are ignored."""
    latest_receipt = golden_receipt.copy()
    latest_receipt["anchors"]["hole1"] = {"x": 10.1, "y": 20, "z": 0} # 0.1mm move
    
    diff = calculate_diff(golden_receipt, latest_receipt, 0.25)
    
    assert not diff["causal_summary"]

def test_anchor_added(golden_receipt):
    """Tests detection of an added anchor."""
    latest_receipt = golden_receipt.copy()
    latest_receipt["anchors"]["new_hole"] = {"x": 100, "y": 100, "z": 0}
    
    diff = calculate_diff(golden_receipt, latest_receipt, 0.25)
    
    assert "new_hole" in diff["causal_summary"]
    assert diff["causal_summary"]["new_hole"]["change_type"] == "added"

def test_anchor_removed(golden_receipt):
    """Tests detection of a removed anchor."""
    latest_receipt = golden_receipt.copy()
    del latest_receipt["anchors"]["hole2"]
    
    diff = calculate_diff(golden_receipt, latest_receipt, 0.25)
    
    assert "hole2" in diff["causal_summary"]
    assert diff["causal_summary"]["hole2"]["change_type"] == "removed"

