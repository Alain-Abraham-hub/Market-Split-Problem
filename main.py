import os
import datetime

from load_and_formulate import parse_marketsplit_dat, formulate_qubo, qubo_to_iskay_dict
from execute import run_iskay_execution
from postprocess import (
    get_latest_result_file,
    load_json_result,
    extract_best_solution,
    validate_split,
    plot_market_split
)

def main():
    print("Starting Market Split Quantum Optimization Pipeline...")
    print("=" * 60)
    
    # ---------------------------------------------------------
    # Setup Paths & Directories
    # ---------------------------------------------------------
    data_file = os.path.join("data", "ms_03_200_177.dat")
    results_dir = "job_results"
    
    # Ensure the job_results directory exists
    os.makedirs(results_dir, exist_ok=True)
    
    # Generate the YYYYMMDD_HHMMSS timestamp for this run
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_json_path = os.path.join(results_dir, f"{timestamp}.json")
    result_plot_path = os.path.join(results_dir, f"{timestamp}_plot.png")
    
    # ---------------------------------------------------------
    # STEP 1: Load Data & Formulate QUBO
    # ---------------------------------------------------------
    print("\n[STEP 1] Data Loading & QUBO Formulation")
    A, b = parse_marketsplit_dat(data_file)
    qubo = formulate_qubo(A, b, "ms_03_200_177")
    iskay_problem = qubo_to_iskay_dict(qubo)
    
    # ---------------------------------------------------------
    # STEP 2 & 3: Quantum Execution (Kipu Iskay Optimizer)
    # ---------------------------------------------------------
    print("\n[STEP 2 & 3] Quantum Execution")
    # Note: Optimization parameters (iterations, shots) are configured inside execute.py.
    # We pass the dynamic save_path to ensure it goes into job_results/YYYYMMDD_HHMMSS.json
    run_iskay_execution(
        iskay_problem=iskay_problem,
        backend_name="auto",
        save_path=result_json_path
    )
    
    # ---------------------------------------------------------
    # STEP 4: Post-Processing & Validation
    # ---------------------------------------------------------
    print("\n[STEP 4] Post-Processing & Validation")
    # Find the most recent file in the job_results directory
    latest_file = get_latest_result_file(results_dir)
    result_data = load_json_result(latest_file)
    
    # Extract the optimal bitstring found by the QPU
    x = extract_best_solution(result_data)
    
    # Validate the mathematical constraint (Ax = b)
    validate_split(x, A, b)
    
    # Visualize and save the plot with the same timestamp
    plot_market_split(x, A, b, save_path=result_plot_path)
    
    print("\n" + "=" * 60)
    print("Pipeline Complete! Check the 'job_results' folder for your outputs.")


if __name__ == "__main__":
    main()

