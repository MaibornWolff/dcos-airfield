
import json
import secrets
import string
from datetime import datetime
from .model import default_configuration
from ..settings.base import DEFAULT_CONFIGURATIONS_FILE, NOTEBOOK_TEMPLATES_FILE


class ConfigurationService:
    """Service that manages possible instance configurations"""
    def __init__(self):
        with open(DEFAULT_CONFIGURATIONS_FILE) as f:
            self._default_configurations = json.load(f)
        with open(NOTEBOOK_TEMPLATES_FILE) as f:
            self._notebook_templates = json.load(f)

    def get_available_configurations(self):
        return self._default_configurations

    def prepare_configuration(self, user_configuration):
        for key, value in default_configuration.items():
            if key in user_configuration and isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in user_configuration[key]:
                        user_configuration[key][sub_key] = sub_value
            elif key not in user_configuration:
                user_configuration[key] = value
        _generate_passwords(user_configuration)
        if "delete_at" in user_configuration and user_configuration["delete_at"] and type(user_configuration["delete_at"]) is str:
            user_configuration["delete_at"] = datetime.strptime(user_configuration["delete_at"], '%Y-%m-%d').timestamp()
        return user_configuration

    def get_available_notebook_templates(self):
        return self._notebook_templates

    def get_notebook_template(self, template_id):
        for template in self._notebook_templates:
            if template["id"] == template_id:
                return template
        return None
    

def _generate_passwords(configuration):
    users = configuration["usermanagement"]["users"]
    for user in users.keys():
        if not users[user]:
            users[user] = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(20))
