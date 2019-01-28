import threading
import requests, time, logging
from .adapters import ZeppelinAdapter


class NotebookTransferThread(threading.Thread):
    """ Thread class with a stop() method.
        This thread will try to upload Zeppelin notebooks to the newly created instance as soon as it is online
    """

    def __init__(self, users, url, template_notebooks=None, import_notebooks=None):
        super(NotebookTransferThread, self).__init__(daemon=True)
        self._stop_event = threading.Event()
        self._template_notebooks = template_notebooks if template_notebooks is not None else []
        self._import_notebooks = import_notebooks if import_notebooks is not None else []
        self._users = users
        self._url = url

    def run(self):
        retry_counter = 120  # the thread will exit after max. 10min - if the Airfield frontend is kept open,
        # the deployment stuck detection will trigger the destruction of this thread earlier
        time.sleep(5)  # so we're not checking before a redeployment started
        # remove templates with the same name as notes to be restored from backup
        import_notebook_names = [note["name"] for note in self._import_notebooks]
        templates = [x for x in self._template_notebooks if x["name"] not in import_notebook_names]
        r = requests.get(self._url + "/api/notebook")
        if len(templates) == 0 and len(self._import_notebooks) == 0:
            return
        while r.status_code != 200 and r.status_code != 405:  # Zeppelin will return 405 if login is necessary
            time.sleep(5)
            r = requests.get(self._url + "/api/notebook")
            retry_counter -= 1
            if retry_counter < 0 or self.stopped():
                logging.error("Notebook import thread has been stopped due to timeout or call")
                return

        if len(self._users) > 0:
            adapter = ZeppelinAdapter(self._url, self._users[0])
        else:
            adapter = ZeppelinAdapter(self._url)

        for notebook in templates:
            adapter.add_notebook(notebook)
        for notebook in self._import_notebooks:
            adapter.import_notebook(notebook)
        logging.info("Import notes on instance " + self._url + " successful")

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()
