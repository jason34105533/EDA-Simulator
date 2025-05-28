class Job:
    def __init__(self, job_id, submit_time, cpu_cores, duration, deadline, license):
        self.job_id = job_id
        self.submit_time = submit_time
        self.cpu_cores = cpu_cores
        self.duration = duration
        self.deadline = deadline
        self.license = license
        self.start_time = None
        self.end_time = None
        self.status = "pending"  # or "running", "completed", "missed_deadline"
        self.where = None # "on-prem" or "cloud"

    def start(self, start_time, where="on-prem"):
        self.start_time = start_time
        self.status = "running"
        self.where = where
    
    def complete(self, end_time):
        self.end_time = end_time
        self.status = "completed"
        
    def is_missed_deadline(self, current_time):
        if self.end_time is None:
            return False
        return self.end_time > self.deadline
        
    def __repr__(self):
        return (f"Job(job_id={self.job_id}, submit_time={self.submit_time}, "
                f"cpu_cores={self.cpu_cores}, duration={self.duration}, "
                f"deadline={self.deadline}, license={self.license}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"status={self.status})")
        
    