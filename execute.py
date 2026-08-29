"""Step 3: Execute Optimization on IBM Quantum via Kipu Iskay Optimizer.

This module handles:
1. Connecting to the IBM Qiskit Functions Catalog.
2. Loading the Kipu Iskay Quantum Optimizer function.
3. Submitting the optimization job to quantum hardware.
4. Monitoring job execution and retrieving the final result.
"""

import json
import os
import time
from typing import Any, Dict, Optional

from qiskit_ibm_catalog import QiskitFunctionsCatalog


def load_iskay_solver(
    token: str,
    instance: str,
    function_id: str = "kipu-quantum/iskay-quantum-optimizer",
):
    """
    Authenticate and load the Iskay Quantum Optimizer from Qiskit Functions Catalog.

    Parameters
    ----------
    token : str
        IBM Quantum API token.
    instance : str
        IBM Quantum instance CRN.
    function_id : str, optional
        Identifier of the Qiskit Function (default: 'kipu-quantum/iskay-quantum-optimizer').

    Returns
    -------
    solver : QiskitFunction
        Loaded solver instance ready to execute optimization jobs.
    """
    print("Connecting to Qiskit Functions Catalog...")
    catalog = QiskitFunctionsCatalog(token=token, instance=instance)
    solver = catalog.load(function_id)
    print(f"  ✓ Loaded function: '{function_id}'")
    return solver


def submit_optimization_job(solver, iskay_input: Dict[str, Any]):
    """
    Submit the optimization payload to the Iskay solver.

    Parameters
    ----------
    solver : QiskitFunction
        Loaded Iskay function instance.
    iskay_input : dict
        Payload containing problem terms, backend, and options.

    Returns
    -------
    job : QiskitFunctionJob
        The running quantum job instance.
    """
    options = iskay_input.get("options", {})
    backend = iskay_input.get("backend_name", "unknown")
    num_terms = len(iskay_input.get("problem", {}))

    print("\nSubmitting Optimization Job to Kipu Quantum:")
    print("=" * 55)
    print(f"  Target Backend        : {backend}")
    print(f"  Problem Size          : {num_terms} QUBO terms")
    print(f"  Algorithm             : bf-DCQO (bias-field counterdiabatic)")
    print(f"  Iterations            : {options.get('num_iterations', 3)}")
    print(f"  Shots / Iteration     : {options.get('shots', 10000):,}")
    print(f"  Preprocessing Level   : {options.get('preprocessing_level', 1)}")
    print(f"  Transpilation Level   : {options.get('transpilation_level', 3)} (Seed: {options.get('seed_transpiler', 42)})")
    print(f"  Postprocessing Level  : {options.get('postprocessing_level', 2)} (3 local search passes)")
    print(f"  Job Tags              : {options.get('job_tags', [])}")
    print("=" * 55)

    job = solver.run(**iskay_input)
    print(f"  ✓ Job submitted successfully!")
    print(f"  → Job ID: {job.job_id}")
    return job


def monitor_and_get_result(job, poll_interval: int = 20) -> Dict[str, Any]:
    """
    Poll the job status until completion and retrieve the result payload.

    Parameters
    ----------
    job : QiskitFunctionJob
        The submitted job instance.
    poll_interval : int, optional
        Polling frequency in seconds (default: 20s).

    Returns
    -------
    dict
        Dictionary containing the optimization results and metadata.
    """
    print(f"\nMonitoring Job Status (Job ID: {job.job_id}):")
    print("-" * 50)

    start_time = time.time()
    while True:
        status = str(job.status())
        elapsed = int(time.time() - start_time)
        print(f"  [{elapsed:>3}s elapsed] Current status: {status:<15}", end="\r", flush=True)

        if status in ["DONE", "CANCELED", "ERROR"]:
            print(f"\n  → Job concluded with final status: {status}")
            break

        time.sleep(poll_interval)

    if str(job.status()) != "DONE":
        raise RuntimeError(f"Job execution did not succeed. Final status: {job.status()}")

    result = job.result()
    print("  ✓ Results downloaded successfully!")
    return result


def save_result_locally(
    result: Dict[str, Any],
    output_path: str = "data/job_result.json",
):
    """Save the retrieved optimization result to disk for offline analysis."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"  ✓ Cached result locally at: {output_path}")


def run_iskay_execution(
    iskay_problem: Dict[str, float],
    options: Optional[Dict[str, Any]] = None,
    backend_name: str = "auto",
    save_path: str = "data/job_result.json",
) -> Dict[str, Any]:
    """
    Complete execution pipeline for Iskay Quantum Optimizer.

    Parameters
    ----------
    iskay_problem : dict
        The Iskay formatted problem dictionary from load_and_formulate.
    options : dict, optional
        Solver tuning options (iterations, shots, levels).
    backend_name : str
        Target backend or 'auto' for least busy QPU.
    save_path : str
        Path where result JSON should be saved.

    Returns
    -------
    dict
        Optimization results returned by the quantum hardware.
    """
    from configure import get_credentials, get_least_busy_backend

    # 1. Default optimization options if not provided
    default_options = {
        "num_iterations": 3,
        "shots": 10000,
        "preprocessing_level": 1,
        "transpilation_level": 3,
        "seed_transpiler": 42,
        "postprocessing_level": 2,
        "job_tags": ["market_split", "iskay_optimization", "qoblib"],
    }
    if options:
        default_options.update(options)

    # 2. Get credentials and determine backend
    creds = get_credentials()
    if backend_name.lower() == "auto":
        backend_name = get_least_busy_backend(creds, min_qubits=20)

    # 3. Construct payload
    iskay_input = {
        "problem": iskay_problem,
        "problem_type": "binary",
        "backend_name": backend_name,
        "options": default_options,
    }

    # 4. Load solver, submit job & wait for result
    solver = load_iskay_solver(token=creds["token"], instance=creds["instance"])
    job = submit_optimization_job(solver, iskay_input)
    result = monitor_and_get_result(job, poll_interval=20)

    # 5. Save result locally
    save_result_locally(result, save_path)
    return result

