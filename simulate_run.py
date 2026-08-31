import os
import json
import datetime
import postprocess
from load_and_formulate import parse_marketsplit_dat

def main():
    print("=" * 60)
    print("MOCK QUANTUM EXECUTION")
    print("=" * 60)
    print("\n1. Generating synthetic quantum results...")
    
    # We classically pre-calculated the exact perfect split for ms_03_200_177.dat
    # so that our synthetic output perfectly satisfies Ax = b
    perfect_bitstring = [0, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1]
    
    # Structure it exactly like the Kipu Iskay JSON response
    mock_result = {
        "optimal_solution": perfect_bitstring,
        "energy": -450.5,
        "metadata": {
            "backend": "ibm_synthetic_simulator",
            "job_id": "mock_job_987654321",
            "execution_time_s": 15.2,
            "status": "DONE"
        }
    }
    
    # Save the synthetic result
    results_dir = "job_results"
    os.makedirs(results_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = os.path.join(results_dir, f"synthetic_{timestamp}.json")
    
    with open(json_path, "w") as f:
        json.dump(mock_result, f, indent=4)
        
    print(f"  ✓ Saved to: {json_path}")
    
    print("\n2. Running standard Post-Processing pipeline...")
    # Load the math problem
    A, b = parse_marketsplit_dat("data/ms_03_200_177.dat")
    
    # Use our existing postprocess functions to parse the synthetic file
    result_data = postprocess.load_json_result(json_path)
    x = postprocess.extract_best_solution(result_data)
    
    # Validate
    postprocess.validate_split(x, A, b)
    
    # Plot
    plot_path = json_path.replace(".json", "_plot.png")
    postprocess.plot_market_split(x, A, b, save_path=plot_path)

if __name__ == "__main__":
    main()

