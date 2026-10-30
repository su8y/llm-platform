from utils.constants import *


def plan_to_status(plan_name:str) -> int:
    if plan_name == PLAN_RUN:
        status = 0
    elif plan_name == PLAN_STOP:
        status = 1
    else:
        status = 999
    return status
