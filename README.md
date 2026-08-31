# Market-Split-Problem

Solving the **Market Split Problem** (from the QOBLIB benchmark) using **Kipu Quantum's Iskay Optimizer** (a Qiskit Function implementing the bf-DCQO algorithm on IBM Quantum hardware).

## Folder & Workflow Structure

```text
Market-Split-Problem/
│
├── data/
│   └── ms_03_200_177.dat        # QOBLIB problem instance
│
├── step1_load_and_formulate.py  # Step 1: Load .dat → build QUBO → convert to Iskay dict
├── step2_configure.py           # Step 2: Set backend, shots, iterations, credentials
├── step3_execute.py             # Step 3: Submit job → poll status → retrieve result
├── step4_postprocess.py         # Step 4: Validate Ax = b → print sales analysis
│
├── main.py                      # Runs all 4 steps in sequence
├── requirements.txt             # Python dependencies
├── msplit/                      # Virtual environment
└── README.md
```

## Quick Start

### 1. Activate Environment & Install Dependencies
```bash
source msplit/bin/activate
pip install -r requirements.txt
```

### 2. Set Credentials
Set your IBM Quantum Platform credentials in your environment:
```bash
export IBM_QUANTUM_TOKEN="<YOUR_API_KEY>"
export IBM_QUANTUM_INSTANCE="<YOUR_INSTANCE_CRN>"
```

### 3. Run the Pipeline

You can run the complete end-to-end pipeline:
```bash
python main.py --instance ms_03_200_177.dat --backend ibm_fez --iterations 3
```

Or test each step individually:
```bash
python step1_load_and_formulate.py
python step2_configure.py
python step3_execute.py
python step4_postprocess.py
```
