class Task:
    def __init__(self, task_id, cpu_cores, duration, license, depends_on=None):
        self.task_id = task_id
        self.cpu_cores = cpu_cores
        self.duration = duration
        self.license = license or []
        self.depends_on = depends_on or []
        
        self.status = "pending"   # pending, running, completed
        self.start_time = None
        
    def start(self, current_time):
        self.start_time = current_time
        self.status = "running"

    def is_ready(self, completed_tasks):
        """Check if this task is ready to run (all dependencies done)."""
        return all(dep in completed_tasks for dep in self.depends_on) and self.status == "pending"