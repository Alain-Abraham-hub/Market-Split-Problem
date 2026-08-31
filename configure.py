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
        channel="ibm_cloud",
        token=creds["token"],
        instance=creds["instance"],
    )

    # Use service.least_busy directly with the filter arguments
    try:
        least_busy = service.least_busy(simulator=False, operational=True, min_num_qubits=min_qubits)
    except Exception as e:
        raise RuntimeError(f"No operational backends found meeting the criteria: {e}")
    print(f"  → Selected least busy backend: {least_busy.name} (Queue: {least_busy.status().pending_jobs} jobs)")
    return least_busy.name




