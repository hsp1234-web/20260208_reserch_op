from src.tasks.base import BaseTask
from datetime import datetime, timedelta

class PCRatioTask(BaseTask):
    def prepare_tasks(self, start_date, end_date):
        tasks = []
        current_date = start_date
        while current_date <= end_date:
            date_slash = current_date.strftime('%Y/%m/%d')
            date_underscore = current_date.strftime('%Y_%m_%d')
            filename = f"PC_Ratio_{date_underscore}.csv"
            url = "https://www.taifex.com.tw/cht/3/dlPcRatioDown"

            tasks.append({
                'task_name': f"PCRatio_{date_underscore}",
                'url': url,
                'save_path': self.get_save_path('B_籌碼分析/PutCall_Ratio', filename),
                'method': 'POST',
                'payload': {
                    'queryStartDate': date_slash,
                    'queryEndDate': date_slash
                },
                'referer': 'https://www.taifex.com.tw/cht/3/dlPcRatio'
            })
            current_date += timedelta(days=1)
        return tasks
