import os
import tempfile
from typing import Optional, Tuple

import numpy as np
import requests
from qiskit_addon_opt_mapper import OptimizationProblem
from qiskit_addon_opt_mapper.converters import OptimizationProblemToQubo


def parse_marketsplit_dat(filename: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Parse a market split problem from a .dat file format.

    Parameters
    ----------
    filename : str
        Path to the .dat file containing the market split problem data.

    Returns
    -------
    A : np.ndarray
        Coefficient matrix of shape (m, n) where m is the number of products
        and n is the number of markets.
    b : np.ndarray
        Target vector of shape (m,) containing the target sales per product.
    """
    with open(filename, "r", encoding="utf-8") as f:
        lines = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]

    if not lines:
        raise ValueError("Empty or invalid .dat file")

    # First line: m n (number of products and markets)
    m, n = map(int, lines[0].split())

    # Next m lines: each row of A followed by corresponding element of b
    A = []
    b = []

    for i in range(1, m + 1):
        values = list(map(int, lines[i].split()))
        A.append(values[:-1])  # First n values: product sales per market
        b.append(values[-1])   # Last value: target sales for this product

    return np.array(A, dtype=np.int32), np.array(b, dtype=np.int32)


def fetch_marketsplit_data(
    instance_name: str = "ms_03_200_177.dat",
) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
    """
    Fetch market split data directly from the QOBLIB repository.

    Parameters
    ----------
    instance_name : str
        Name of the .dat file to fetch from the repository.

    Returns
    -------
    A : np.ndarray or None
        Coefficient matrix of shape (m, n) if successful, None if failed.
    b : np.ndarray or None
        Target vector of shape (m,) if successful, None if failed.
    """
    url = (
        "https://git.zib.de/qopt/qoblib-quantum-optimization-benchmarking-library"
        f"/-/raw/main/01-marketsplit/instances/{instance_name}"
    )

    try:
        # Fetch the file content with timeout
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".dat", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(response.text)
            temp_file_path = temp_file.name

        try:
            # Use our parsing function to extract A and b
            A, b = parse_marketsplit_dat(temp_file_path)
            return A, b
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass  # File cleanup failure is not critical

    except requests.RequestException as e:
        print(f"Error fetching data from repository: {e}")
        return None, None
    except (ValueError, IOError, OSError) as e:
        print(f"Error processing data: {e}")
        return None, None


def formulate_qubo(A: np.ndarray, b: np.ndarray, problem_name: str = "market_split"):
    """
    Convert the constrained Market Split problem (Ax = b) to an unconstrained QUBO.

    Parameters
    ----------
    A : np.ndarray
        Coefficient matrix of shape (m, n).
    b : np.ndarray
        Target vector of shape (m,).
    problem_name : str, optional
        Name of the optimization problem.

    Returns
    -------
    qubo : OptimizationProblem
        The converted QUBO optimization problem.
    """
    # Create optimization problem
    ms = OptimizationProblem(problem_name)

    # Add binary variables (one for each market)
    ms.binary_var_list(A.shape[1])

    # Add equality constraints (one for each product)
    for idx, rhs in enumerate(b):
        ms.linear_constraint(A[idx, :], sense="==", rhs=int(rhs))

    # Convert to QUBO with penalty parameter
    qubo = OptimizationProblemToQubo(penalty=1).convert(ms)
    return qubo


def qubo_to_iskay_dict(qubo) -> dict:
    """
    Convert a Qiskit QUBO problem into the dictionary format required by Iskay.

    Notes
    -----
    For binary variables where x_i in {0, 1}, we have x_i^2 = x_i.
    Linear terms '(i, )' combine the original linear coefficient with the diagonal
    quadratic coefficient (b_i + c_{ii}).
    Off-diagonal quadratic terms are stored under keys '(i, j)' with i < j.
    """
    iskay_input_problem = {"()": float(qubo.objective.constant)}
    num_vars = qubo.get_num_vars()

    linear_dict = qubo.objective.linear.to_dict()
    quadratic_dict = qubo.objective.quadratic.to_dict()

    for i in range(num_vars):
        for j in range(i, num_vars):
            if i == j:
                # Add linear term (combining linear and diagonal quadratic contributions)
                lin_val = float(linear_dict.get(i, 0.0) or 0.0)
                diag_val = float(quadratic_dict.get((i, i), 0.0) or 0.0)
                iskay_input_problem[f"({i}, )"] = lin_val + diag_val
            else:
                # Add off-diagonal quadratic term
                quad_val = float(quadratic_dict.get((i, j), 0.0) or 0.0)
                if quad_val != 0.0:
                    iskay_input_problem[f"({i}, {j})"] = quad_val

    return iskay_input_problem


if __name__ == "__main__":
    # Load the problem instance
    instance_name = "ms_03_200_177.dat"
    local_path = os.path.join("data", instance_name)
    
    if os.path.exists(local_path):
        print(f"Loading local instance from {local_path}...")
        A, b = parse_marketsplit_dat(local_path)
    else:
        print(f"Fetching {instance_name} from QOBLIB...")
        A, b = fetch_marketsplit_data(instance_name=instance_name)

    if A is not None:
        print("Successfully loaded problem instance from QOBLIB")
        print("\nProblem Instance Analysis:")
        print("=" * 50)
        print(f"Coefficient Matrix A: {A.shape[0]} × {A.shape[1]}")
        print(f"   → {A.shape[0]} products (constraints)")
        print(f"   → {A.shape[1]} markets (decision variables)")
        print(f"Target Vector b: {b}")
        print("   → Target sales per product for each region")
        print(
            f"Solution Space: "
            f"2^{A.shape[1]} = {2**A.shape[1]:,} possible assignments"
        )

        # Convert to QUBO
        qubo = formulate_qubo(A, b, instance_name.replace(".dat", ""))

        print("\nQUBO Conversion Complete:")
        print("=" * 50)
        print(f"Number of variables: {qubo.get_num_vars()}")
        print(f"Constant term: {qubo.objective.constant}")
        print(f"Linear terms: {len(qubo.objective.linear.to_dict())}")
        print(f"Quadratic terms: {len(qubo.objective.quadratic.to_dict())}")

        # Convert to Iskay dictionary format
        iskay_problem = qubo_to_iskay_dict(qubo)

        print("\nIskay Dictionary Format:")
        print("=" * 50)
        print(f"Total coefficients: {len(iskay_problem)}")
        print(f"  • Constant term: {iskay_problem['()']}")
        print(
            f"  • Linear terms: "
            f"{sum(1 for k in iskay_problem.keys() if k != '()' and ', )' in k)}"
        )
        print(
            f"  • Quadratic terms: "
            f"{sum(1 for k in iskay_problem.keys() if k != '()' and ', )' not in k)}"
        )
        print("\nSample coefficients (first 5):")
        for k, v in list(iskay_problem.items())[:5]:
            coeff_type = "constant" if k == "()" else "linear" if ", )" in k else "quadratic"
            print(f"  {k}: {v} ({coeff_type})")

