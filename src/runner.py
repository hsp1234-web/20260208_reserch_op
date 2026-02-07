import os
import argparse
from datetime import datetime, timedelta
from src.downloader import TaifexDownloader
from src.tasks.futures_tick import FuturesTickTask
from src.tasks.options_tick import OptionsTickTask
from src.tasks.pc_ratio import PCRatioTask
from src.tasks.options_delta import OptionsDeltaTask
from src.tasks.annual_market import AnnualMarketTask

def run(start_date, end_date,
        base_dir='data/raw',
        max_workers=8,
        enabled_tasks=None,
        download_annual=False,
        start_year=None,
        end_year=None):

    downloader = TaifexDownloader(max_workers=max_workers)
    tasks_to_run = []

    if enabled_tasks is None:
        enabled_tasks = ['futures_tick', 'options_tick', 'pc_ratio', 'options_delta']

    # Initialize task objects
    if 'futures_tick' in enabled_tasks:
        tasks_to_run.extend(FuturesTickTask(base_dir).prepare_tasks(start_date, end_date))

    if 'options_tick' in enabled_tasks:
        tasks_to_run.extend(OptionsTickTask(base_dir).prepare_tasks(start_date, end_date))

    if 'pc_ratio' in enabled_tasks:
        tasks_to_run.extend(PCRatioTask(base_dir).prepare_tasks(start_date, end_date))

    if 'options_delta' in enabled_tasks:
        tasks_to_run.extend(OptionsDeltaTask(base_dir).prepare_tasks(start_date, end_date))

    if download_annual:
        am_task = AnnualMarketTask(base_dir)
        if start_year and end_year:
            tasks_to_run.extend(am_task.prepare_annual_tasks(start_year, end_year))
        else:
            tasks_to_run.extend(am_task.prepare_tasks(start_date, end_date))

    if not tasks_to_run:
        print("No tasks to execute. Please check your configuration.")
        return

    print(f"Starting execution of {len(tasks_to_run)} tasks with {max_workers} workers...")
    results = downloader.run_parallel(tasks_to_run)

    success_count = sum(1 for r in results if r['status'] == 'success')
    not_found_count = sum(1 for r in results if r['status'] == 'not_found')
    error_count = len(results) - success_count - not_found_count

    print(f"\nExecution Summary:")
    print(f"  Success: {success_count}")
    print(f"  Not Found: {not_found_count}")
    print(f"  Errors: {error_count}")

if __name__ == "__main__":
    # Default: last 30 days
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=30)

    run(start_dt, end_dt)
