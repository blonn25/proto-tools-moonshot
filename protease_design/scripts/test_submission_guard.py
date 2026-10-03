"""Check scheduler representations that affect the aggregate GPU limit."""

import pytest

from submit_gpu import count_reserved_gpus


def test_counts_pending_and_running_but_preserves_other_projects():
    queue = (
        "101|protease-gpu|protease_design|RUNNING|gres/gpu:1|1\n"
        "102|protease-gpu|protease_design|PENDING|gres/gpu:nvidia_h100_nvl:1|1\n"
        "103|other-project|none|RUNNING|gres/gpu:8|1\n"
        "104|protease-cpu|protease_design|RUNNING|N/A|1\n"
    )
    assert count_reserved_gpus(queue) == 2

def test_counts_multiple_nodes():
    assert count_reserved_gpus("105|protease-gpu||RUNNING|gres/gpu:1|2") == 2

@pytest.mark.parametrize("row", [
    "106|protease-gpu||RUNNING|N/A|1",
    "107_[1-9%2]|protease-gpu||PENDING|gres/gpu:1|1",
    "108|protease-gpu||RUNNING|unknown|1",
])
def test_refuses_ambiguous_gpu_jobs_and_arrays(row):
    with pytest.raises(ValueError, match="allocation"):
        count_reserved_gpus(row)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q", "-c", "/dev/null", "-p", "no:cacheprovider"]))
