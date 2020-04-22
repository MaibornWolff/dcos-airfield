"""Static base settings for the application"""

import os


APP_STATIC_FOLDER = os.path.join(os.getcwd(), "frontend", "dist")
ZEPPELIN_MARATHON_FILE = os.path.join(os.getcwd(), "airfield", "resources", "zeppelin_marathon.json")
JUPYTER_MARATHON_FILE = os.path.join(os.getcwd(), "airfield", "resources", "jupyter_marathon.json")
SHIRO_CONF_FILE = os.path.join(os.getcwd(), "airfield", "resources", "shiro.ini.jinja2")
DEFAULT_CONFIGURATIONS_FILE = os.path.join(os.getcwd(), "airfield", "resources", "default_configurations.json")
NOTEBOOK_TEMPLATES_FILE = os.path.join(os.getcwd(), "airfield", "resources", "notebook_templates.json")

## Flask settings

APP_SECRET = 'super-secret-key'
SESSION_TYPE = 'filesystem'