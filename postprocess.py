import os
import glob
import json
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Any, Tuple, Optional


def get_latest_result_file(results_dir: str = "job_results") -> str:
    """
    Find and return the path to the most recently created JSON file in the results directory.
    """
    if not os.path.exists(results_dir):
        raise FileNotFoundError(f"The directory '{results_dir}' does not exist.")
    
    json_files = glob.glob(os.path.join(results_dir, "*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON result files found in '{results_dir}'.")
    
    # Sort files by modification time and pick the most recent one
    latest_file = max(json_files, key=os.path.getmtime)
    print(f"Found latest result file: {latest_file}")
    return latest_file


def load_json_result(file_path: str) -> Dict[str, Any]:
    """Load the JSON result from the specified file path."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_best_solution(result_data: Dict[str, Any]) -> np.ndarray:
    """
    Extract the best bitstring from the Iskay JSON result.
    Accounts for various standard Qiskit / Iskay dictionary structures.
    """
    x = None
    if "optimal_solution" in result_data:
        x = result_data["optimal_solution"]
    elif "solution" in result_data:
        x = result_data["solution"]
    elif "samples" in result_data and len(result_data["samples"]) > 0:
        # Often a list of dicts: [{"state": "101...", "energy": -50.0}, ...]
        sample = result_data["samples"][0]
        x = sample.get("state", sample)
    else:
        raise KeyError(f"Could not find the solution in the result keys: {list(result_data.keys())}")
        
    # Convert a bitstring like "10110" or a list of floats to a numpy array of integers
    if isinstance(x, str):
        x = [int(bit) for bit in x]
    
    return np.array(x, dtype=int)


def validate_split(x: np.ndarray, A: np.ndarray, b: np.ndarray) -> Tuple[bool, np.ndarray]:
    """
    Check if the assigned market split (x) perfectly matches the target (b).
    """
    # Calculate how many of each product are allocated to Region A (where x_i = 1)
    allocated_to_A = np.dot(A, x)
    
    # Calculate the difference from our ideal target
    difference = allocated_to_A - b
    is_valid = np.all(difference == 0)
    
    print("\n--- Validation Results ---")
    print(f"Target allocations (b)    : {b}")
    print(f"Actual allocations (A*x)  : {allocated_to_A}")
    print(f"Difference (A*x - b)      : {difference}")
    
    if is_valid:
        print("✅ SUCCESS: Valid Split! The quantum solver found a perfect solution.")
    else:
        print("❌ FAILURE: Invalid Split. The allocations do not perfectly match the targets.")
        
    return is_valid, difference


def plot_market_split(x: np.ndarray, A: np.ndarray, b: np.ndarray, save_path: Optional[str] = None):
    """
    Plot a bar chart comparing the product allocations between Region A and Region B,
    including the target split line.
    """
    allocated_to_A = np.dot(A, x)
    total_items = A.sum(axis=1)
    allocated_to_B = total_items - allocated_to_A
    
    num_products = len(b)
    products = np.arange(num_products)
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create side-by-side bars for Region A and Region B
    ax.bar(products - width/2, allocated_to_A, width, label='Region A (Quantum Solution)', color='#4C72B0')
    ax.bar(products + width/2, allocated_to_B, width, label='Region B (Remainder)', color='#DD8452')
    
    # Overlay the target goals (b)
    for i, target in enumerate(b):
        ax.hlines(target, i - width, i + width, color='black', linestyle='--', linewidth=2, 
                  label='Target (b)' if i == 0 else "")
        
    ax.set_ylabel('Total Items Allocated')
    ax.set_title('Market Split Problem: Product Allocation by Region')
    ax.set_xticks(products)
    ax.set_xticklabels([f"Product {i+1}" for i in products])
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Ensure plot directory exists if saving
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches="tight")
        print(f"\nPlot saved to {save_path}")
    
    plt.show()

if __name__ == "__main__":
    # This block is here for testing postprocess.py individually.
    # It assumes data/ms_03_200_177.dat exists and a job_results directory has at least one json file.
    import sys
    
    try:
        from load_and_formulate import parse_marketsplit_dat
        
        A, b = parse_marketsplit_dat("data/ms_03_200_177.dat")
        latest_file = get_latest_result_file("job_results")
        result_data = load_json_result(latest_file)
        
        x = extract_best_solution(result_data)
        print(f"\nExtracted Bitstring:\n{x}")
        
        validate_split(x, A, b)
        plot_market_split(x, A, b)
        
    except FileNotFoundError as e:
        print(f"Cannot run standalone test: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

