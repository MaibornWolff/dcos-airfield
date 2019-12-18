"""Handles Zeppelin interactions."""

import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class ZeppelinAdapter:
    def __init__(self, base_host):
        self.base_host = base_host
        self.session = requests.Session()

    def login(self, username, password):
        try:
            r = self.session.post(self.base_host + '/api/login', data={"userName": username, "password": password})
        except ConnectionError:
            raise ZeppelinException("Login at Zeppelin instance " + self.base_host + " was unsuccessful.")
        if not r.ok:
            raise ZeppelinException("Login at Zeppelin instance " + self.base_host + " was unsuccessful.")

    def add_notebook(self, notebook):
        r = self.session.post(self.base_host + '/api/notebook', json=notebook)
        if not r.ok:
            raise ZeppelinException(r.text)
        return r

    def import_notebook(self, notebook):
        r = self.session.post(self.base_host + '/api/notebook/import', json=notebook)
        if not r.ok:
            raise ZeppelinException(r.text)
        return r

    def export_notebook(self, id):
        r = self.session.get(self.base_host + '/api/notebook/export/'+id)
        if not r.ok:
            raise ZeppelinException(r.text)
        content = r.json()
        notebook = json.loads(content["body"])
        for paragraph in notebook.get("paragraphs", list()):
            if "results" in paragraph:
                del paragraph["results"]  # Clear out results as they are not needed and can blow up json size
        return notebook

    def list_notebooks(self):
        r = self.session.get(self.base_host + '/api/notebook')
        if not r.ok:
            raise ZeppelinException(r.text)
        return r.json()["body"]

    def ping(self):
        try:
            response = self.session.get(self.base_host + '/api/notebook')
            return response.status_code == 200 or response.status_code == 405  # Zeppelin will return 405 if login is necessary
        except:
            return False


class ZeppelinException(Exception):
    pass
