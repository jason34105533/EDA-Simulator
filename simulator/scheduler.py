from simulator.job import Job
from simulator.resource_manager import ResourceManager

class Scheduler:
    def __init__(self, resource_manager):
        """
        Initialize the Scheduler with a resource manager and time quantum.
        
        :param resource_manager: The resource manager to handle resources.
        :param time_quantum: The time quantum for scheduling (default is 1).
        """
        self.job_queue: list[Job] = []
        self.resource_manager: ResourceManager = resource_manager
        self.current_time = 0
        

    def set_current_time(self, time):
        """
        Set the current simulation time.
        
        :param time: The current time to be set.
        """
        self.current_time = time
        # print(f"Current simulation time set to {self.current_time}.")
    
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
        # print available resources
        print(f"Available CPU cores: {self.resource_manager.get_available_cores()}")
        print(f"Available licenses: {self.resource_manager.licenses}")
        for job in self.job_queue:
            
            job.update_status(self.current_time)
            
            if job.status == 'missed_deadline':
                print(f"Job '{job.job_id}' has missed its deadline.")
                continue
            elif job.status == 'pending':
                    if self.resource_manager.can_schedule_job(job):
                        self.resource_manager.allocate_resources(job)
                        job.start(self.current_time)
                        print(f"Job '{job.job_id}' scheduled successfully.")
                    else:
                        print(f"Job '{job.job_id}' cannot be scheduled at this moment due to resource constraints.")
            elif job.status == 'running':
                if self.current_time >= job.start_time + job.duration:
                    job.complete(self.current_time)
                    self.resource_manager.release_resources(job)
                    print(f"Job '{job.job_id}' completed at time {self.current_time}.")
                else:
                    print(f"Job '{job.job_id}' is still running.")
            elif job.status == 'completed':
                print(f"Job '{job.job_id}' is already completed at time {job.end_time}.")
            else:
                print(f"Job '{job.job_id}' has an unknown status: {job.status}")
                
    
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

    