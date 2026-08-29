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
    postprocessing_level: int = 2,
    job_tags: Optional[list] = None,
) -> Dict[str, Any]:
    """
    Build the payload dictionary required by the Iskay Quantum Optimizer.

    Parameters
    ----------
    iskay_problem_dict : Dict[str, float]
        Dictionary of QUBO/HUBO terms formatted for Iskay.
    creds : dict
        Credentials dictionary for querying backend status if 'auto'.
    backend_name : str
        Target IBM Quantum backend or 'auto' for the least busy (default: 'auto').
    num_iterations : int
        Number of bias-field iterations (default: 3).
    shots : int
        Number of shots per iteration (default: 10000).
    postprocessing_level : int
        Local search refinement passes (default: 2, meaning 3 passes).
    job_tags : list, optional
        Custom tags for tracking jobs in the IBM Quantum platform.

    Returns
    -------
    dict
        The payload dictionary to pass to `iskay_solver.run(**payload)`.
    """
    if backend_name.lower() == "auto":
        # Problem requires exactly as many qubits as variables
        # (Minus 1 for the constant term '()' if we just count keys vaguely, but let's be safe)
        num_vars = sum(1 for k in iskay_problem_dict.keys() if ", )" in k)
        backend_name = get_least_busy_backend(creds, min_qubits=max(num_vars, 20))
    options = {
        "num_iterations": num_iterations,
        "shots": shots,
        "postprocessing_level": postprocessing_level,
        "job_tags": job_tags or ["market_split_optimization"],
    }

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

