import logging
import time
from multiprocessing import Pool

import config.chat_spider_config as cfg
from core.dataset_manager import DatasetManager
from core.driver_initilizer import DriverInitializer
from core.history_manager import HistoryManager
from core.single_task_spider import SingleTaskSpider

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def __run_single_task(history: HistoryManager, uid: str, bv: str):
    logging.debug(f'📄 Task (bv={bv}) executing...')
    driver = DriverInitializer.get_firefox_driver()
    data = SingleTaskSpider(driver).get_reply_records(bv)
    DatasetManager().save_single_task(uid=uid, bv=bv, data=data)
    history.single_task_completed(uid=uid, bv=bv)
    driver.close()
    driver.quit()
    logging.info(f'📄 Task (bv={bv}) completed: {len(data)} records saved.')


def __load(uid, bv_list: list):
    pool = Pool(cfg.max_parallel_job_num)

    for bv in bv_list:
        pool.apply_async(func=__run_single_task, args=(HistoryManager, uid, bv))
        time.sleep(3)

    pool.close()
    pool.join()


def run_specified(uid: str, bv_list: list):
    if len(bv_list) == 0:
        return

    logging.info(f'📦 Job (uid={uid}) loaded. {len(bv_list)} video specified.')
    __load(uid, bv_list)
    logging.info(f'📦 Job (uid={uid}) completed.')


def run(uid: str):
    # If the job is completed then return straightly
    if HistoryManager.is_job_completed(uid):
        return

    logging.info(f'📦 Job (uid={uid}) loaded.')
    __load(uid, HistoryManager.get_uncompleted_tasks(uid))
    logging.info(f'📦 Job (uid={uid}) completed.')
