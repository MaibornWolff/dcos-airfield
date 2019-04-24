# -*- coding: utf-8 -*-
"""Handles Zeppelin interactions."""

#  standard imports
import json
# third party imports
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class ZeppelinAdapter(object):
    def __init__(self, base_host, user=None):
        self.base_host = base_host
        self.session = requests.Session()
        self._login(user)

    def _login(self, user):
        if user is None:
            return
        else:
            try:
                r = self.session.post(self.base_host + '/api/login', data={"userName": user["username"],
                                                                           "password": user["password"]})
            except ConnectionError:
                raise ZeppelinException("Login at Zeppelin instance " + self.base_host + " was unsuccessful.")
            if r.ok:
                return
            else:
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
        return r


class ZeppelinException(Exception):
    pass
