class Job:
    def __init__(self, job_id: int, submit_time: int, cpu_cores: int, duration: int, deadline: int, license: dict):
        
        # Static attributes
        self.job_id = job_id
        self.submit_time = submit_time
        self.cpu_cores = cpu_cores
        self.duration = duration
        self.deadline = deadline
        self.license = license
        
        # Runtime attributes
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
                f"cpu_cores={self.cpu_cores}, duration={self.duration}, "
                f"deadline={self.deadline}, license={self.license}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"status={self.status})")
        
    