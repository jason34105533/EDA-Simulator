from job_submitter.submitter import JobSubmitter
from simulator.scheduler import Scheduler
from simulator.resource_manager import ResourceManager
from simulator.job import Job

'''
Instatiate Job submitter, call load_workflow.
Instantiate Scheduler, call add_job and schedule_jobs.

A simple infinite loop to simulate the passage of time and check for deadlines.
Stop when all jobs are completed.

Calculate the performance metrics: Wait Time, Turnaround Time, and Deadline Miss Rate. And the Money Cost. 
'''

def stop_simulation():
    print("Stopping simulation...")
    exit(0)
    
TIME_QUANTUM = 5  # Define the time quantum for the simulation

if __name__ == "__main__":
    print("Starting EDA Job Scheduling Simulation...")

    # Instantiate ResourceManager
    resource_manager = ResourceManager('config/infra_config.yaml')

    # Instantiate Scheduler
    scheduler = Scheduler(resource_manager)
    
    # Instantiate JobSubmitter and load workflow
    job_submitter = JobSubmitter('workflow/workflow_1.yaml', scheduler)

    
    time = 0  # Initialize simulation time
    scheduler.set_current_time(time)
    job_submitter.set_current_time(time)
    
    # stop_simulation()
    # Simulate time passage and check for deadlines
    while not (scheduler.all_jobs_completed() and job_submitter.all_jobs_submitted()):
        # Increment time by the time quantum
        time += TIME_QUANTUM
        print(f"\n--- Simulation Time: {time} ---")
        scheduler.set_current_time(time)
        job_submitter.set_current_time(time)

        job_submitter.submit_jobs()
        scheduler.schedule_jobs()

    # Calculate performance metrics
    # scheduler.calculate_performance_metrics()
    
    print("Simulation completed.")