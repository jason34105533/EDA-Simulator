class Scheduler:
    def __init__(self, simulation):
        job_queue = []
        on_prem_resources = []
        cloud_resources = []
        licenses = []

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
    
    
        