"""tests/_cuda_probe.py.

Prove each visible GPU can execute CUDA, using only the NVIDIA driver library.

``nvidia-smi`` only shows that the driver can see hardware; a container without
device access or a driver mismatch still lists GPUs that CUDA cannot use. This
probe initialises CUDA through ``libcuda.so.1`` (shipped with the driver), then
opens a context and allocates one byte on every visible device. It needs no
framework, so the test environment stays free of torch. Tool environments carry
their own framework builds, which the GPU tests themselves exercise.

Run as a script so no CUDA state outlives the probe: it prints the usable
device count and a reason separated by a tab, and exits non-zero when no
device can run CUDA.
"""

from __future__ import annotations

import ctypes
import os
import sys


def _error_name(cuda: ctypes.CDLL, code: int) -> str:
    """Return the driver's name for a ``CUresult`` code, falling back to the number."""
    name = ctypes.c_char_p()
    if cuda.cuGetErrorName(code, ctypes.byref(name)) == 0 and name.value:
        return name.value.decode()
    return f"CUresult {code}"


def probe() -> tuple[int, str]:
    """Count the visible GPUs that can execute CUDA.

    Returns:
        tuple[int, str]: Usable device count (0 if any device fails) and a reason
            suitable for a skip message.
    """
    cvd = os.environ.get("CUDA_VISIBLE_DEVICES")
    if cvd is not None and cvd.strip() == "":
        return 0, "CUDA_VISIBLE_DEVICES hides all devices"
    try:
        cuda = ctypes.CDLL("libcuda.so.1")
    except OSError:
        return 0, "libcuda.so.1 not found (no NVIDIA driver)"

    if (rc := cuda.cuInit(0)) != 0:
        return 0, f"cuInit failed: {_error_name(cuda, rc)}"
    count = ctypes.c_int()
    if (rc := cuda.cuDeviceGetCount(ctypes.byref(count))) != 0:
        return 0, f"cuDeviceGetCount failed: {_error_name(cuda, rc)}"

    for index in range(count.value):
        device, context, pointer = ctypes.c_int(), ctypes.c_void_p(), ctypes.c_uint64()
        # ctypes objects are read when each call runs, so later steps see what earlier ones wrote.
        steps = (
            ("cuDeviceGet", cuda.cuDeviceGet, (ctypes.byref(device), index)),
            ("cuCtxCreate", cuda.cuCtxCreate_v2, (ctypes.byref(context), 0, device)),
            ("cuMemAlloc", cuda.cuMemAlloc_v2, (ctypes.byref(pointer), ctypes.c_size_t(1))),
            ("cuMemFree", cuda.cuMemFree_v2, (pointer,)),
            ("cuCtxDestroy", cuda.cuCtxDestroy_v2, (context,)),
        )
        for name, function, args in steps:
            if (rc := function(*args)) != 0:
                return 0, f"{name} failed on GPU {index}: {_error_name(cuda, rc)}"
    return count.value, f"CUDA ran on {count.value} GPU(s)"


if __name__ == "__main__":
    usable, reason = probe()
    print(f"{usable}\t{reason}")
    sys.exit(0 if usable else 1)
