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
