# coding=UTF-8

import init_environ

import datetime

from apps.mnt.models_task import MntTaskMng, MntTask

def main():

    shop_id = 63518068

    start_time = datetime.datetime.now()
    MntTaskMng.check_routine_task(shop_id)

    tasks = MntTask.objects.filter(shop_id = shop_id, create_time__gte = start_time, task_type = 0)
    for task in tasks:
        task.run()

if __name__ == '__main__':
    main()
