#External Import
import random


#[15, 21, 27, 33, 35, 39, 51, 55, 57, 65, 69, 77, 85, 87, 91, 93, 95]
import random

IBM_API_KEY = "IhZU3kWeBIFyTBIC7vURVmxAXeYi4SwxXD-rHhFLOwTF"

# IBM Quantum instance CRN, required alongside IBM_API_KEY when using a fresh token.
IBM_INSTANCE_CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/517b9f446b9e4c38b0b8d5f1866cd573:e62eb19a-3850-4ccb-bbc2-50d213f1c45d::"


def GiveN():
    N_list = [57]
    return random.choice(N_list)
#[39,57,21, 35]

def GiveN():
	N_list = [57]
	N = random.choice(N_list)
	return N