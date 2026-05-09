import json
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import time

class TaskScheduler:
    """定时任务管理器，负责任务的持久化和调度"""
    def __init__(self, config_dir="./config", on_task_trigger=None):
        self.config_dir = config_dir
        self.tasks_file = os.path.join(config_dir, "scheduled_tasks.json")
        self.scheduler = BackgroundScheduler()
        self.on_task_trigger = on_task_trigger
        self.tasks = {}
        self.running = False
        self._load_tasks()

    def start(self):
        """启动调度器"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            for task_id, task in self.tasks.items():
                if task.get('enabled', True):
                    self._schedule_task(task_id, task)

    def stop(self):
        """停止调度器"""
        if self.running:
            self.scheduler.shutdown()
            self.running = False

    def _load_tasks(self):
        """从文件加载任务列表"""
        if not os.path.exists(self.tasks_file):
            os.makedirs(self.config_dir, exist_ok=True)
            self._save_tasks()
            return
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = data.get('tasks', {})
        except Exception as e:
            print(f"加载定时任务失败: {e}")

    def _save_tasks(self):
        """保存任务列表到文件"""
        try:
            data = {'tasks': self.tasks}
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存定时任务失败: {e}")

    def _schedule_task(self, task_id, task):
        """调度单个任务"""
        trigger = task.get('trigger')
        trigger_args = task.get('trigger_args', {})
        try:
            if trigger == 'cron':
                cron = trigger_args.get('cron')
                if cron:
                    self.scheduler.add_job(
                        func=self._trigger_task,
                        trigger=CronTrigger.from_crontab(cron),
                        args=[task_id],
                        id=task_id,
                        replace_existing=True
                    )
            elif trigger == 'interval':
                seconds = trigger_args.get('seconds', 0)
                if seconds > 0:
                    self.scheduler.add_job(
                        func=self._trigger_task,
                        trigger=IntervalTrigger(seconds=seconds),
                        args=[task_id],
                        id=task_id,
                        replace_existing=True
                    )
            elif trigger == 'date':
                run_date = trigger_args.get('run_date')
                if run_date:
                    run_date_obj = datetime.fromisoformat(run_date)
                    self.scheduler.add_job(
                        func=self._trigger_task,
                        trigger=DateTrigger(run_date=run_date_obj),
                        args=[task_id],
                        id=task_id,
                        replace_existing=True
                    )
        except Exception as e:
            print(f"调度任务 {task_id} 失败: {e}")

    def _trigger_task(self, task_id):
        """任务触发时的回调"""
        task = self.tasks.get(task_id)
        if task and task.get('enabled', True):
            if self.on_task_trigger:
                message = task.get('message', '')
                self.on_task_trigger(message)
            if task.get('trigger') == 'date':
                self.remove_task(task_id)

    def add_task(self, task_info):
        """添加新任务，返回任务ID"""
        task_id = str(int(time.time() * 1000))
        task_info['id'] = task_id
        task_info['enabled'] = task_info.get('enabled', True)
        self.tasks[task_id] = task_info
        if self.running and task_info['enabled']:
            self._schedule_task(task_id, task_info)
        self._save_tasks()
        return task_id

    def update_task(self, task_id, updates):
        """更新任务"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            if self.running:
                # 安全移除旧任务
                job = self.scheduler.get_job(task_id)
                if job:
                    job.remove()
                if self.tasks[task_id].get('enabled', True):
                    self._schedule_task(task_id, self.tasks[task_id])
            self._save_tasks()

    def remove_task(self, task_id):
        """删除任务"""
        if task_id in self.tasks:
            if self.running:
                # 安全移除任务
                job = self.scheduler.get_job(task_id)
                if job:
                    job.remove()
            del self.tasks[task_id]
            self._save_tasks()

    def get_tasks(self):
        """获取所有任务列表"""
        tasks_list = []
        for task_id, task in self.tasks.items():
            task_copy = task.copy()
            task_copy['id'] = task_id
            tasks_list.append(task_copy)
        return tasks_list
