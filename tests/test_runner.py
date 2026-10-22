from rampwatch.runner import percentile, check_target
import pytest
def test_percentile():
    assert percentile([1,2,3,4,5], 50) == 3
    assert percentile([], 95) == 0.0
def test_local_only():
    with pytest.raises(ValueError):
        check_target('http://example.com/')
    check_target('http://127.0.0.1:8080/')
