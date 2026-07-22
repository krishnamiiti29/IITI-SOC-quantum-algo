"""
User-configurable settings for the factoring pipeline.
Edit the values below, then run runner.py.
"""

# Candidate N values (composite integers) the pipeline picks from at random.
N_VALUES = [14]

# IBM Quantum API key. Leave as None to fall back to locally saved account
# credentials (set up once via QiskitRuntimeService.save_account(...)).
IBM_API_KEY = "tqE3sq1TH4GUAyIgaz6QLxr3VCC60TW3UnjJFZAlusfG"

# IBM Quantum instance CRN, required alongside IBM_API_KEY when using a fresh token.
IBM_INSTANCE_CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/517b9f446b9e4c38b0b8d5f1866cd573:e62eb19a-3850-4ccb-bbc2-50d213f1c45d::"
