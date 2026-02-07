from src.tasks.base import BaseTask
import os

class AnnualMarketTask(BaseTask):
    def prepare_annual_tasks(self, start_year, end_year):
        tasks = []
        for year in range(start_year, end_year + 1):
            # Futures Annual Report
            tasks.append({
                'task_name': f"AnnualFutures_{year}",
                'url': "https://www.taifex.com.tw/cht/3/futDataDown",
                'save_path': self.get_save_path('年度歷史資料', f"AnnualFutures_{year}.csv"),
                'method': 'POST',
                'payload': {
                    'down_type': '2',
                    'his_year': str(year)
                },
                'referer': 'https://www.taifex.com.tw/cht/3/dlFutDailyMarketView'
            })

            # Options Annual Report
            tasks.append({
                'task_name': f"AnnualOptions_{year}",
                'url': "https://www.taifex.com.tw/cht/3/optDataDown",
                'save_path': self.get_save_path('年度歷史資料', f"AnnualOptions_{year}.csv"),
                'method': 'POST',
                'payload': {
                    'down_type': '2',
                    'his_year': str(year)
                },
                'referer': 'https://www.taifex.com.tw/cht/3/dlOptDailyMarketView'
            })
        return tasks

    def prepare_tasks(self, start_date, end_date):
        # Override BaseTask's prepare_tasks to handle years covered by the date range
        start_year = start_date.year
        end_year = end_date.year
        return self.prepare_annual_tasks(start_year, end_year)
