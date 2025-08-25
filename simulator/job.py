from simulator.task import Task
from simulator.license import License

class Job:
    def __init__(self, job_id: int, submit_time: int, cpu_cores: int, deadline: int, license: list[License], tasks: list[Task]):
        """
        Initializes a Job instance with the given parameters.
        """
        
        # Static attributes
        self.job_id = job_id
        self.submit_time = submit_time
        self.cpu_cores = cpu_cores
        self.using_cpu_cores = 0
        self.deadline = deadline
        self.license = license
        self.tasks: list[Task] = tasks
        
        # Runtime attributes
        self.run_cluster = None
        self.start_time = None
        self.end_time = None
        self.status = "pending"  # or "running", "completed", "missed_deadline"
        self.where = None # "on-prem" or "cloud"
    
    def __lt__(self, other):
        """
        Less than comparison for priority queue ordering.
        Primary: submit_time (earlier jobs have higher priority)
        Secondary: job_id (for deterministic ordering when submit_times are equal)
        """
        if self.submit_time != other.submit_time:
            return self.submit_time < other.submit_time
        return self.job_id < other.job_id
    
    # Task Level Functions
    def ready_tasks(self) -> list[Task]:
        completed = {t.task_id for t in self.tasks if t.status == "completed"}
        return [t for t in self.tasks if t.status == "pending" and t.is_ready(completed)]
    
    def run(self, current_time):
        if self.status != "running":
            return
        

        # 1) advance running tasks
        for task in self.tasks:
            if task.status == "running":
                if task.start_time + task.duration <= current_time:
                    task.status = "completed"
                    self.cpu_cores += task.cpu_cores  # return cores to job's pool
                    self.using_cpu_cores -= task.cpu_cores
                    print(f"Task {task.task_id} of Job {self.job_id} completed at time {current_time}.")
                else:
                    # print(f"Task {task.task_id} of Job {self.job_id} is still running.") #[Log]
                    pass
                    
        # 2) start ready tasks
        # print(f"Job {self.job_id} at time {current_time}: trying to start ready tasks. Using cores: {self.using_cpu_cores}/{self.cpu_cores}") #[Log]
        # print(f"Ready tasks: {[t.task_id for t in self.ready_tasks()]}") #[Log]
        
        for task in self.ready_tasks():
            if self.cpu_cores >= task.cpu_cores:
                task.status = "running"
                self.cpu_cores -= task.cpu_cores
                self.using_cpu_cores += task.cpu_cores
                task.start(current_time)
    
    def all_completed(self):
        return all(t.status == "completed" for t in self.tasks)
        
    
    # Job Level Functions

    def start(self, start_time, where="on-prem"):
        self.start_time = start_time
        self.status = "running"
        self.where = where
    
    def complete(self, end_time):
        self.end_time = end_time
        self.status = "completed"
        
    def is_completed(self):
        return self.status == "completed" or self.status == "missed_deadline"
    
        
    def update_status(self, current_time):
        if ((self.status == "pending") and current_time >= self.deadline):
            self.status = "missed_deadline"
        
    def __repr__(self):
        return (f"Job(job_id={self.job_id}, submit_time={self.submit_time}, "
                f"cpu_cores={self.cpu_cores}, "
                f"deadline={self.deadline}, license={self.license}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"status={self.status})")
        
    