import random

IBM_API_KEY = "FBhUm9RPg6zwtUwt99FfIV7JLouJW2cqfmFnuPTceZhZ"
IBM_INSTANCE_CRN = "crn:v1:bluemix:public:quantum-computing:us-east:a/517b9f446b9e4c38b0b8d5f1866cd573:e62eb19a-3850-4ccb-bbc2-50d213f1c45d::"

# Valid tests, try to increase these [57, 95, 111, 123]
def GiveN():
    N_list = [57]
    return random.choice(N_list)