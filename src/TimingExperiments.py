
experiment_delay_type_E_configs = [{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": range(1, 21),
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": range(1, 6), "Transport": 2}
},{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": 2,
        "Transport": range(1, 21)
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": range(1, 6)}
}, {
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": range(1, 21),
        "Forklift": 2,
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": range(1, 6), "Forklift": 2, "Transport": 2}
}]

experiment_delay_type_S_configs = [{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "S", "Forklift": "S", "Transport": "S"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": range(1, 21),
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": range(1, 6), "Transport": 2}
},{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "S", "Forklift": "S", "Transport": "S"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": 2,
        "Transport": range(1, 21)
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": range(1, 6)}
}, {
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "S", "Forklift": "S", "Transport": "S"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": range(1, 21),
        "Forklift": 2,
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": range(1, 6), "Forklift": 2, "Transport": 2}
}]

experiment_logsize_configs = [{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 2,
    "branch_tracking": True,
    "log_size": range(50,1501,50),
    "delay_amount": {
        "Door": 2,
        "Forklift": 2,
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": 2}
}]

experiment_loopbound_configs = [{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": range(1,10),
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": 2,
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": 2}
}]

experiment_configs_test = [{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 1,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": range(1, 5),
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": range(1, 3), "Transport": 2}
},{
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 1,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": 2,
        "Forklift": 2,
        "Transport": range(1, 5)
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": range(1, 3)}
}, {
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 1,
    "branch_tracking": True,
    "log_size": -1,
    "delay_amount": {
        "Door": range(1, 5),
        "Forklift": 2,
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": 2}
}, {
    "verifyta_path": "",
    "base_path": "",
    "delay_type": {"Door": "E", "Forklift": "E", "Transport": "E"},
    "loop_bound": 1,
    "branch_tracking": True,
    "log_size": range(50,501,50),
    "delay_amount": {
        "Door": 2,
        "Forklift": 2,
        "Transport": 2
    },
    "subsets": "SubsetA",
    "role_amount": {"Door": 1, "Forklift": 2, "Transport": 2}
}]

def get_scaling_experiments():
    result = []
    result.extend(experiment_delay_type_E_configs)
    result.extend(experiment_delay_type_S_configs)
    result.extend(experiment_logsize_configs)
    result.extend(experiment_loopbound_configs)
    return result
