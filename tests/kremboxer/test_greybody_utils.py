"""
test_greybody_utils - Test suite

This code provides the test suite. It can be run through the pytest
unit testing framework.

New bug reports for the code should not be closed without ensuring that
a test in the suite both fails before the fix, and passes after it.
"""

import pytest
import numpy as np

import kremboxer.greybody_utils as gbu


def test_planck_model():
    """
    Test the polynomial approximation of the Planck model
    """
    # Test the Planck model against the known value at 300 K
    A = 3
    T = 300
    N = 3.2
    test_val = A * T ** N

    assert np.isclose(gbu.planck_model(T, A, N), test_val, atol=1e-12)

