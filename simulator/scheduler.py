class Scheduler:
    def __init__(self, resource_manager):
        """
        Initialize the Scheduler with a resource manager and time quantum.
        
        :param resource_manager: The resource manager to handle resources.
        :param time_quantum: The time quantum for scheduling (default is 1).
        """
        self.job_queue = []
        self.resource_manager = resource_manager
        self.licenses = []
        self.current_time = 0
        

    def set_current_time(self, time):
        """
        Set the current simulation time.
        
        :param time: The current time to be set.
        """
        self.current_time = time
        print(f"Current simulation time set to {self.current_time}.")
    
    def add_job(self, job):
        """
        Add a job to the job queue.
        
        :param job: The job to be added.
        """
        self.job_queue.append(job)
        print(f"Job '{job.job_id}' added to the queue.")
        
    def schedule_jobs(self):
        """
        Schedule jobs based on their submission time and resource requirements.
        This method will iterate through the job queue and allocate resources
        based on the availability of CPU cores and licenses.
        """
        for job in self.job_queue:
            if self.can_schedule_job(job):
                self.allocate_resources(job)
                print(f"Job '{job.job_id}' scheduled successfully.")
            else:
                print(f"Job '{job.job_id}' cannot be scheduled due to resource constraints.")
    
    def check_deadlines(self, current_time):
        """
        Check if any jobs have missed their deadlines.
        
        :param current_time: The current simulation time.
        """
        for job in self.job_queue:
            if job.is_missed_deadline(current_time):
                print(f"Job '{job.job_id}' has missed its deadline.")
                
    def all_jobs_completed(self):
        """
        Check if all jobs in the job queue are completed.
        
        :return: True if all jobs are completed, False otherwise.
        """
        for job in self.job_queue:
            if not job.is_completed():
                return False
        return True

    