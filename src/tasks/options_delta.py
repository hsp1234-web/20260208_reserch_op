from src.tasks.base import BaseTask
from datetime import datetime, timedelta

class OptionsDeltaTask(BaseTask):
    def prepare_tasks(self, start_date, end_date):
        tasks = []
        current_date = start_date
        while current_date <= end_date:
            date_nodash = current_date.strftime('%Y%m%d')
            date_underscore = current_date.strftime('%Y_%m_%d')
            filename = f"Delta_{date_nodash}.csv"
            url = f"https://www.taifex.com.tw/file/taifex/Dailydownload/delta/chinese/Delta_{date_nodash}.csv"

            tasks.append({
                'task_name': f"OptionsDelta_{date_underscore}",
                'url': url,
                'save_path': self.get_save_path('B_籌碼分析/選擇權Delta', filename),
                'method': 'GET'
            })
            current_date += timedelta(days=1)
        return tasks
