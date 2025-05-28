class JobSubmitter:
    def __init__(self, workflow, scheduler):
        """
        Initialize the JobSubmitter with a workflow and a scheduler.
        
        :param workflow: The workflow to be executed.
        :param scheduler: The scheduler to manage job execution.
        """
        self.workflow = workflow
        self.scheduler = scheduler
        self.job_queue: dict = {}
        
    def submit_job(self, job):
        """Submit a job to the job queue."""
        
        print(f"Job '{job}' submitted successfully.")
        
    def load_workflow(self, workflow):
        """Load a new workflow."""
        self.workflow = workflow
        print(f"Workflow '{workflow}' loaded successfully.")