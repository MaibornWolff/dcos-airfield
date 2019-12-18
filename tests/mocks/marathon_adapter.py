


class MarathonAdapterMock:
    def deploy_instance(self, app_definition):
        self._value_deploy_instance = app_definition
    
    def value_deploy_instance(self):
        return self._value_deploy_instance

    def get_instance_status(self, app_id):
        return self._value_get_instance_status
    
    def value_get_instance_status(self, value):
        self._value_get_instance_status = value

    def delete_instance(self, app_id):
        self._value_delete_instance = app_id
        return True
    
    def restart_instance(self, app_id):
        self._value_restart_instance = app_id
    
    def value_restart_instance(self):
        return self._value_restart_instance

    def stop_instance(self, app_id):
        self._value_stop_instance = app_id
    
    def value_stop_instance(self):
        return self._value_stop_instance

    def start_instance(self, app_id):
        self._value_start_instance = app_id
    
    def value_start_instance(self):
        return self._value_start_instance

    def get_instance_ip_address_and_port(self, app_id):
        return "127.0.0.1", 0