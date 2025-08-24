import heapq
import yaml
from simulator.job import Job
from simulator.license import License

class JobSubmitter:
    def __init__(self, workflow_path, scheduler):
        """
        Initialize the JobSubmitter with a workflow and a scheduler.
        
        :param workflow: The workflow to be executed.
        :param scheduler: The scheduler to manage job execution.
        """
        self.job_queue = self._load_workflow_from_file(workflow_path)
        heapq.heapify(self.job_queue)  # Ensure it's a valid heap
        
        self.scheduler = scheduler
        
        # print loaded jobs for verification
        # while self.job_queue:
        #     job = heapq.heappop(self.job_queue)
        #     print(f"Loaded job: {job}")
        
        self.current_time = 0
        
    def _load_workflow_from_file(self, workflow_path):
        """Load workflow from YAML file and convert to Job objects."""
        try:
            with open(workflow_path, 'r') as file:
                workflow_data = yaml.safe_load(file)
            
            jobs: list[Job] = []
            for job_data in workflow_data.get('jobs', []):
                # Parse licenses
                licenses: list[License] = []
                for license_data in job_data.get('license', []):
                    license = License(
                        license_name=license_data['license_name'],
                        license_count=license_data['license_count']
                    )
                    licenses.append(license)
                
                # Create Job object
                job = Job(
                    job_id=job_data['job_id'],
                    submit_time=job_data['submit_time'],
                    cpu_cores=job_data['cpu_cores'],
                    duration=job_data['duration'],
                    deadline=job_data['deadline'],
                    license=licenses
                )
                jobs.append(job)
            
            print(f"Loaded workflow '{workflow_data.get('workflow_name', 'Unknown')}' with {len(jobs)} jobs.")
            return jobs
                
        except FileNotFoundError:
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in workflow: {e}")
                
        
    def set_current_time(self, time):
        """Set the current simulation time."""
        self.current_time = time
        print(f"Current simulation time set to {self.current_time}.")    
    
    def submit_job(self, job):
        """Submit a job to the job queue."""
        
        print(f"Job '{job}' submitted successfully.")
        
    def submit_jobs(self):
        """Submit all jobs in the workflow to the scheduler."""
        for job in self.workflow:
            if job['job_id'] not in self.job_queue:
                self.job_queue[job['job_id']] = job
                self.submit_job(job)
                self.scheduler.add_job(job)
            else:
                print(f"Job '{job['job_id']}' is already in the queue.")
        
        
    def load_workflow(self, workflow):
        """Load a new workflow."""
        self.workflow = workflow
        print(f"Workflow '{workflow}' loaded successfully.")
        
    def all_jobs_completed(self):
        """Check if all jobs in the workflow are completed."""
        for job in self.workflow:
            if not job.is_completed():
                return False
        return True
        