import heapq
import yaml
from simulator.job import Job
from simulator.task import Task
from simulator.license import License
from simulator.scheduler import Scheduler


class JobSubmitter:
    def __init__(self, workflow_path, scheduler):
        """
        Initialize the JobSubmitter with a workflow and a scheduler.
        
        :param workflow: The workflow to be executed.
        :param scheduler: The scheduler to manage job execution.
        """
        self.job_queue = self._load_workflow_from_file(workflow_path)
        # sort jobs by submit_time and job_id for deterministic processing order
        self.job_queue.sort()
        
        self.scheduler: Scheduler = scheduler
        
        # print loaded jobs for verification
        for job in self.job_queue:
            print(f"Loaded job: {job}")  #[Log]
            pass
        
        self.current_time = 0
        
    def _load_workflow_from_file(self, workflow_path):
        """Load workflow from YAML file and convert to Job objects."""
        try:
            with open(workflow_path, 'r') as file:
                workflow_data = yaml.safe_load(file)
            
            jobs: list[Job] = []
            for job_data in workflow_data.get('jobs', []):
                tasks: list[Task] = []
                for task_data in job_data.get('tasks', []):
                    
                    # Parse licenses
                    licenses: list[License] = []
                    for license_data in task_data.get('licenses', []):
                        license = License(
                            license_name=license_data['license_name'],
                            license_count=license_data['license_count']
                        )
                        licenses.append(license)
                        
                    task = Task(
                        task_id=task_data['task_id'],
                        cpu_cores=task_data['cpu_cores'],
                        duration=task_data['duration'],
                        license=licenses,
                        depends_on=task_data.get('depends_on', [])
                    )
                    tasks.append(task)
                    
                # Aggregate licenses for the job from its tasks
                license_dict = {}
                for task in tasks:
                    for lic in task.license:
                        if lic.license_name in license_dict:
                            license_dict[lic.license_name] += lic.license_count
                        else:
                            license_dict[lic.license_name] = lic.license_count
                licenses = [License(name, count) for name, count in license_dict.items()]
                
                
                # Create Job object
                job = Job(
                    job_id=job_data['job_id'],
                    submit_time=job_data['submit_time'],
                    cpu_cores=40,
                    deadline=job_data['deadline'],
                    license=licenses,
                    tasks=tasks
                )
                jobs.append(job)
                

            for job in jobs:
                print(f"Loaded job: {job.job_id} with submit time {job.submit_time} and deadline {job.deadline}.")  #[Log]
            
            print(f"Loaded workflow '{workflow_data.get('workflow_name', 'Unknown')}' with {len(jobs)} jobs.")  #[Log]
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
        
    def submit_jobs(self):
        """Submit all jobs whose submit_time <= current_time to the scheduler."""
        while self.job_queue and self.job_queue[0].submit_time <= self.current_time:
            job = self.job_queue.pop(0)
            self.scheduler.add_job(job)
            print(f"Job '{job.job_id}' submitted to scheduler at time {self.current_time}.")

        # print(f"Current job queue length: {len(self.job_queue)}")   #[Log]
        
    def all_jobs_submitted(self):
        """Check if all jobs are submitted."""
        return len(self.job_queue) == 0
        
        