from __future__ import annotations

from ..kernels import Kernel, validate_kernel
from ..model import Problem


def validate_kernel_records(kernel: Kernel) -> tuple[Problem, ...]:
    return validate_kernel(kernel)
