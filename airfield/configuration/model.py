"""Default and dummy instance configuration"""


default_configuration = {
    "type": "zeppelin",  # zeppelin or jupyter
    "notebook": {
        "cores": 1,
        "memory": 1024,
    },
    "spark": {
        "python_version": "python3",  # python2 or python3
        "executor_memory": 1024,
        "executor_cores": 1,
        "cores_max": 4,
    },
    "admin": {
        "group": None,
        "admins": []
    },
    "usermanagement": {
        "enabled": False,
        "password": None,  # only for jupyter
        "users": {}  # key: username, value: password, only for zeppelin, None as password gets random generated passwords
    },
    "libraries": {
        "python": [],
        "r": [],
    },
    "delete_at": None,
    "comment": ""
}