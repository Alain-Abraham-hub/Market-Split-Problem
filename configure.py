import os
from typing import Any, Dict, Optional

from qiskit_ibm_runtime import QiskitRuntimeService


def get_credentials() -> Dict[str, str]:
    """
    Retrieve IBM Quantum API credentials directly from the embedded code.
    
    IMPORTANT: Do not commit your actual token or CRN to public version control!
    """
    ibm_token = "ikTWj5DigvDSGgGxDZPSrfV0rSJXqaHlTSMzXRfiMCjo"
    ibm_instance = "crn:v1:bluemix:public:quantum-computing:us-east:a/94761ff6d3874e7289dcdd83673edbcf:44f44ef9-fe70-4cf5-a4d7-bf3d79da147b::"

    return {
        "token": ibm_token,
        "instance": ibm_instance,
    }


def get_least_busy_backend(creds: Dict[str, str], min_qubits: int = 20) -> str:
    """
    Connect to IBM Quantum and find the operational backend with the shortest queue.

    Parameters
    ----------
    creds : dict
        Dictionary containing 'token' and 'instance'.
    min_qubits : int
        Minimum number of qubits required for the problem (default: 20 for MS-200-177).

    Returns
    -------
    str
        The name of the least busy backend.
    """
    print(f"Connecting to IBM Quantum to find the least busy backend (>={min_qubits} qubits)...")
    service = QiskitRuntimeService(
        channel="ibm_quantum",
        token=creds["token"],
        instance=creds["instance"],
    )

    # Filter for real hardware that is operational and large enough
    backends = service.backends(simulator=False, operational=True, min_num_qubits=min_qubits)
    
    if not backends:
        raise RuntimeError("No operational backends found meeting the criteria.")

    least_busy = service.least_busy(backends)
    print(f"  → Selected least busy backend: {least_busy.name} (Queue: {least_busy.status().pending_jobs} jobs)")
    return least_busy.name


def build_iskay_input(
    iskay_problem_dict: Dict[str, float],
    creds: Dict[str, str],
    backend_name: str = "auto",
    num_iterations: int = 3,
    shots: int = 10000,
    preprocessing_level: int = 1,
    transpilation_level: int = 3,
    seed_transpiler: Optional[int] = 42,
    postprocessing_level: int = 2,
    job_tags: Optional[list] = None,
    extra_options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build the full optimization payload for Kipu Quantum's Iskay Optimizer.

    Parameters
    ----------
    iskay_problem_dict : Dict[str, float]
        Dictionary of QUBO terms formatted as {'()': const, '(i, )': lin, '(i, j)': quad}.
    creds : dict
        Credentials dictionary for resolving 'auto' backend selection.
    backend_name : str
        Target IBM Quantum backend (or 'auto' for the operational QPU with shortest queue).
    num_iterations : int
        Number of bias-field (bf-DCQO) iterations (default: 3, range: 1-10).
    shots : int
        Measurement shots per iteration (default: 10000, range: 100-100000).
    preprocessing_level : int
        Problem reduction level: 0 (None), 1 (Standard), 2 (Aggressive).
    transpilation_level : int
        Qiskit circuit transpiler optimization level (default: 3, range: 0-3).
    seed_transpiler : int, optional
        RNG seed for deterministic circuit layout and routing (default: 42).
    postprocessing_level : int
        Local search passes on measured bitstrings: 0 (1 pass), 1 (2 passes), 2 (3 passes).
    job_tags : list, optional
        Custom tags for identifying this job in the IBM Quantum dashboard.
    extra_options : dict, optional
        Additional vendor options to pass to the solver.

    Returns
    -------
    dict
        The payload dictionary ready to pass directly to `iskay_solver.run(**iskay_input)`.
    """
    if backend_name.lower() == "auto":
        num_vars = sum(1 for k in iskay_problem_dict.keys() if ", )" in k)
        backend_name = get_least_busy_backend(creds, min_qubits=max(num_vars, 20))

    options: Dict[str, Any] = {
        # Algorithm configuration
        "num_iterations": num_iterations,
        "shots": shots,

        # Preprocessing & Transpilation
        "preprocessing_level": preprocessing_level,
        "transpilation_level": transpilation_level,

        # Postprocessing
        "postprocessing_level": postprocessing_level,

        # Tracking
        "job_tags": job_tags or ["market_split", "iskay_optimization", "qoblib"],
    }

    if seed_transpiler is not None:
        options["seed_transpiler"] = seed_transpiler

    if extra_options:
        options.update(extra_options)

    iskay_input = {
        "problem": iskay_problem_dict,
        "problem_type": "binary",
        "backend_name": backend_name,
        "options": options,
    }

    return iskay_input


if __name__ == "__main__":
    # Quick sanity check for the payload builder
    sample_problem = {"()": 0.0, "(0, )": -5.0, "(0, 1)": 4.0}
    
    creds = get_credentials()
    print("Credentials Check:")
    print("=" * 40)
    print(f"  Token loaded: {creds['token'] != 'PASTE_YOUR_IBM_QUANTUM_TOKEN_HERE'}")
    print(f"  Instance loaded: {creds['instance'] != 'PASTE_YOUR_INSTANCE_CRN_HERE'}")

    # Fallback to ibm_fez if no real credentials are provided so the test doesn't crash
    test_backend = "auto" if creds["token"] != "PASTE_YOUR_IBM_QUANTUM_TOKEN_HERE" else "ibm_fez"
    
    payload = build_iskay_input(
        iskay_problem_dict=sample_problem,
        creds=creds,
        backend_name=test_backend
    )

    print("\nIskay Optimizer Configuration Payload:")
    print("=" * 40)
    print(f"  Backend: {payload['backend_name']}")
    print(f"  Problem Type: {payload['problem_type']}")
    print(f"  Iterations: {payload['options']['num_iterations']}")
    print(f"  Shots: {payload['options']['shots']}")
    print(f"  Postprocessing Level: {payload['options']['postprocessing_level']}")
    print(f"  Job Tags: {payload['options']['job_tags']}")

