from __future__ import annotations

import os
from typing import Any


def load_ibm_backend_from_env(*, min_qubits: int) -> Any:
    """Load an IBM Quantum backend from env vars, guarded against accidental paid use."""
    token = os.getenv("IBM_QUANTUM_TOKEN")
    instance = os.getenv("IBM_QUANTUM_INSTANCE")
    backend_name = os.getenv("IBM_QUANTUM_BACKEND", "least_busy")
    allow_paid = os.getenv("IBM_QUANTUM_ALLOW_PAID", "false").lower() == "true"

    if not token:
        raise RuntimeError("IBM_QUANTUM_TOKEN is required for IBM hardware runs")
    if not instance:
        raise RuntimeError("IBM_QUANTUM_INSTANCE is required for IBM hardware runs")
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "IBM hardware runs require qiskit-ibm-runtime. Install/update requirements first."
        ) from exc

    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
        instance=instance,
    )

    if not allow_paid:
        _assert_open_usage_available(service)

    if backend_name == "least_busy":
        backend = service.least_busy(operational=True, simulator=False, min_num_qubits=min_qubits)
    else:
        backend = service.backend(backend_name)
    return IBMRuntimeBackend(backend)


class IBMRuntimeBackend:
    """Small adapter that gives IBM Runtime SamplerV2 the backend.run/result/get_counts shape."""

    def __init__(self, backend: Any) -> None:
        self._backend = backend

    def run(self, circuit: Any, *, shots: int) -> "IBMRuntimeJob":
        try:
            from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
            from qiskit_ibm_runtime import SamplerV2 as Sampler
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "IBM hardware runs require qiskit-ibm-runtime and compatible qiskit packages."
            ) from exc

        pass_manager = generate_preset_pass_manager(optimization_level=1, backend=self._backend)
        isa_circuit = pass_manager.run(circuit)
        sampler = Sampler(mode=self._backend)
        runtime_job = sampler.run([isa_circuit], shots=shots)
        return IBMRuntimeJob(runtime_job)


class IBMRuntimeJob:
    def __init__(self, runtime_job: Any) -> None:
        self._runtime_job = runtime_job

    def result(self) -> "IBMRuntimeResult":
        return IBMRuntimeResult(self._runtime_job.result())


class IBMRuntimeResult:
    def __init__(self, primitive_result: Any) -> None:
        self._primitive_result = primitive_result

    def get_counts(self) -> dict[str, int]:
        pub_result = self._primitive_result[0]
        data = pub_result.data
        for register_name in ("meas", "c", "cr"):
            register = getattr(data, register_name, None)
            if register is not None and hasattr(register, "get_counts"):
                return register.get_counts()
        for value in vars(data).values():
            if hasattr(value, "get_counts"):
                return value.get_counts()
        raise RuntimeError("Could not extract counts from IBM Runtime Sampler result")


def _assert_open_usage_available(service: Any) -> None:
    try:
        service.usage()
    except Exception as exc:
        raise RuntimeError(
            "Could not verify Open/free IBM Quantum usage. "
            "Refusing to run while IBM_QUANTUM_ALLOW_PAID=false."
        ) from exc
