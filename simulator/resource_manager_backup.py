import yaml
import os

from simulator.job import Job
from simulator.license import License

class ResourceManager:
    def __init__(self, config):
        
        self.resources = {}
        self.licenses = {}
        
        # Parse the YAML configuration file
        if os.path.exists(config):
            with open(config, 'r') as file:
                config_data = yaml.safe_load(file)
        else:
            raise FileNotFoundError(f"Configuration file not found: {config}")

        # Initialize resources from config
        if 'resources' in config_data:
            resources_config = config_data['resources']
            
            # Initialize on-prem resources
            if 'on_prem' in resources_config:
                self.resources['on_prem'] = {
                    'total_cores': resources_config['on_prem'].get('total_cpu_cores', 0),
                    'available_cores': resources_config['on_prem'].get('total_cpu_cores', 0),
                    'max_jobs': resources_config['on_prem'].get('max_jobs_on_prem', 0)
                }
            
            # Initialize cloud resources
            if 'cloud' in resources_config:
                self.resources['cloud'] = {
                    'provider': resources_config['cloud'].get('provider', ''),
                    'max_cores': resources_config['cloud'].get('max_cpu_cores', 0),
                    'available_cores': resources_config['cloud'].get('max_cpu_cores', 0),
                    'cost_per_cpu_minute': resources_config['cloud'].get('cost_per_cpu_minute', 0.0)
                }
            
            # Initialize license limits
            if 'license_limits' in resources_config:
                for license_type, count in resources_config['license_limits'].items():
                    self.licenses[license_type] = count

        # Store other configuration settings
        self.config_data = config_data
        
        print(f"ResourceManager initialized with config: {config_data}")
        print(f"Resources: {self.resources}")
        print(f"Licenses: {self.licenses}")
        

    def get_available_cores(self):
        """
        Returns the number of available CPU cores for a job on prem.
        """
        return self.resources['on_prem']['available_cores']
    
    def allocate_cores(self, required_cores):
        """
        Allocates CPU cores for a job if available.
        Returns True if allocation is successful, False otherwise.
        """
        if self.resources['on_prem']['available_cores'] >= required_cores:
            self.resources['on_prem']['available_cores'] -= required_cores
            return True
        return False
    
    def release_cores(self, cores):
        """
        Releases allocated CPU cores back to the resource pool.
        """
        self.resources['on_prem']['available_cores'] += cores
    
    def get_available_licenses(self, job_license):
        """
        Returns the number of available license in a single type.
        """
        return self.licenses.get(job_license, 0)
    
    def allocate_license(self, job_license, number_of_license=1):
        """
        Allocates that type of licenses for a job if available.
        Returns True if allocation is successful, False otherwise.
        """
        if self.licenses.get(job_license, 0) >= number_of_license:
            self.licenses[job_license] -= number_of_license
            return True
        return False
    
    def release_license(self, job_license, number_of_license=1):
        """
        Releases allocated licenses back to the resource pool.
        """
        if job_license in self.licenses:
            self.licenses[job_license] += number_of_license
        else:
            self.licenses[job_license] = number_of_license
            
    def can_schedule_job(self, job: Job):
        """
        Check if a job can be scheduled based on available CPU cores and licenses.
        
        :param job: The job to be checked.
        :return: True if the job can be scheduled, False otherwise.
        """
        # Check CPU core availability
        if self.get_available_cores() < job.cpu_cores:
            return False
        
        # Check license availability
        for license in job.license:
            if self.get_available_licenses(license.license_name) < license.license_count:
                return False
        
        return True
    

    def can_schedule_job_on_cloud(self, job: Job):
        """
        Check if a job can be scheduled on cloud based on available CPU cores.
        
        :param job: The job to be checked.
        :return: True if the job can be scheduled on cloud, False otherwise.
        """
        # Check CPU core availability on cloud
        if self.resources['cloud']['available_cores'] >= job.cpu_cores:
            for license in job.license:
                if self.get_available_licenses(license.license_name) < license.license_count:
                    return False
            return True
        return False
    
    def allocate_resources_on_cloud(self, job):
        """
        Allocate resources (CPU cores and licenses) for a job on cloud.
        
        :param job: The job for which resources are to be allocated.
        :return: True if resources are successfully allocated, False otherwise.
        """
        
        # Allocate licenses
        for license in job.license:
            if not self.allocate_license(license.license_name, license.license_count):
                return False
        
        return True
    
    
    def allocate_resources(self, job):
        """
        Allocate resources (CPU cores and licenses) for a job.
        
        :param job: The job for which resources are to be allocated.
        :return: True if resources are successfully allocated, False otherwise.
        """
        # Allocate CPU cores
        if not self.allocate_cores(job.cpu_cores):
            return False
        
        # Allocate licenses
        for license in job.license:
            if not self.allocate_license(license.license_name, license.license_count):
                # If license allocation fails, release previously allocated cores
                self.release_cores(job.cpu_cores)
                return False
        
        return True
        
    def release_resources(self, job):
        """
        Release resources (CPU cores and licenses) allocated to a job.
        :param job: The job for which resources are to be released.
        """
        # Release CPU cores
        self.release_cores(job.cpu_cores)
        
        # Release licenses
        for license in job.license:
            self.release_license(license.license_name, license.license_count)
            
    
        


    