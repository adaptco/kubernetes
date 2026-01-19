
import pytest
import os
import json
from scripts.cam_runner import generate_receipt

def test_generate_receipt_success():
    """
    Tests that a receipt is generated successfully for an existing file.
    """
    # Create a dummy CAD file for the test
    dummy_cad_path = "test.cad"
    with open(dummy_cad_path, "w") as f:
        f.write("dummy cad data")

    receipt = generate_receipt(dummy_cad_path)
    
    assert receipt is not None
    assert receipt["metadata"]["source_file"] == "test.cad"
    assert "anchors" in receipt
    assert "mounting_hole_1" in receipt["anchors"]

    # Clean up the dummy file
    os.remove(dummy_cad_path)

def test_generate_receipt_file_not_found():
    """
    Tests that the function raises FileNotFoundError for a non-existent file.
    """
    with pytest.raises(FileNotFoundError):
        generate_receipt("non_existent_file.cad")

