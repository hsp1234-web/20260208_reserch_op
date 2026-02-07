from abc import ABC, abstractmethod
import os

class BaseTask(ABC):
    def __init__(self, base_dir):
        self.base_dir = base_dir

    @abstractmethod
    def prepare_tasks(self, start_date, end_date):
        """
        Returns a list of task dicts for the downloader.
        """
        pass

    def get_save_path(self, sub_dir, filename):
        path = os.path.join(self.base_dir, sub_dir)
        os.makedirs(path, exist_ok=True)
        return os.path.join(path, filename)
