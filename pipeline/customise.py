"""
User-configurable settings for the factoring pipeline.
Edit the values below, then run runner.py.
"""

# Candidate N values (composite integers) the pipeline picks from at random.
N_VALUES = [14]

# IBM Quantum API key. Leave as None to fall back to locally saved account
# credentials (set up once via QiskitRuntimeService.save_account(...)).
IBM_API_KEY = "p-vLEG5nbvMFyOGQf1ckc0SVcziTeXS6fm_ChFGrcCRK"

# IBM Quantum instance CRN, required alongside IBM_API_KEY when using a fresh token.
IBM_INSTANCE_CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/173eafa31b95438e87efcb6e706391b2:eb07dbb1-7a94-4ff7-bcde-7b9c32b8b8c6::"
