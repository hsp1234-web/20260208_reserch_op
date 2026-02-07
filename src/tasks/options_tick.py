from src.tasks.base import BaseTask
from datetime import datetime, timedelta

class OptionsTickTask(BaseTask):
    def prepare_tasks(self, start_date, end_date):
        tasks = []
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y_%m_%d')
            filename = f"OptionsDaily_{date_str}.zip"
            url = f"https://www.taifex.com.tw/file/taifex/Dailydownload/OptionsDailydownloadCSV/{filename}"

            tasks.append({
                'task_name': f"OptionsTick_{date_str}",
                'url': url,
                'save_path': self.get_save_path('A_核心交易/選擇權逐筆', filename),
                'method': 'GET'
            })
            current_date += timedelta(days=1)
        return tasks
