import yaml
import os

from simulator.job import Job
from simulator.license import License

class ResourceManager:
    def __init__(self, config):
        self.resources = {}
        self.licenses = {}
        self.cost_per_cpu_minute = 0.0
        
        # Parse the YAML configuration file
        if os.path.exists(config):
            with open(config, 'r') as file:
                config_data = yaml.safe_load(file)
        else:
            raise FileNotFoundError(f"Configuration file not found: {config}")

        # Initialize resources from config
        if 'resources' in config_data:
            resources_config = config_data['resources']
            
            # On-prem clusters
            # On-prem clusters
            if 'on_prem' in resources_config:
                cpu_per_node = resources_config['on_prem'].get('cpu_cores_per_node', 0)
                nodes_per_cluster = resources_config['on_prem'].get('nodes_per_cluster', 0)
                num_clusters = resources_config['on_prem'].get('number_of_clusters', 1)

                cores_per_cluster = cpu_per_node * nodes_per_cluster

                self.resources['on_prem'] = {
                    'cores_per_cluster': cores_per_cluster,
                    'clusters': [cores_per_cluster for _ in range(num_clusters)],
                    'max_jobs': resources_config['on_prem'].get('max_jobs_on_prem', 0)
                }
            
            # Cloud
            if 'cloud' in resources_config:
                self.resources['cloud'] = {
                    'provider': resources_config['cloud'].get('provider', ''),
                    'available_cores': resources_config['cloud'].get('available_cores', 0),
                    'cost_per_cpu_minute': resources_config['cloud'].get('cost_per_cpu_minute', 0.0)
                }
            
                self.cost_per_cpu_minute = resources_config['cloud'].get('cost_per_cpu_minute', 0.0)
            # License limits
            if 'license_limits' in resources_config:
                for license_type, count in resources_config['license_limits'].items():
                    self.licenses[license_type] = count

        self.config_data = config_data
        
        print(f"ResourceManager initialized with config: {config_data}")
        print(f"Resources: {self.resources}")
        print(f"Licenses: {self.licenses}")
        

    def get_available_cores(self):
        """Return total available cores across all clusters."""
        return (self.resources['on_prem']['clusters'])
    
    def allocate_cores(self, required_cores, cluster_idx):
        """
        Try to allocate cores from a specific cluster.
        Returns True if successful.
        """
        if self.resources['on_prem']['clusters'][cluster_idx] >= required_cores:
            self.resources['on_prem']['clusters'][cluster_idx] -= required_cores
            return True
        return False
    
    def release_cores(self, cores, cluster_idx):
        """Release cores back to a specific cluster."""
        self.resources['on_prem']['clusters'][cluster_idx] += cores
    
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
            
    def can_schedule_job(self, job: Job) -> int:
        """
        Check if job can run on its assigned cluster.
        Assumes scheduler already set job.run_cluster.
        """

        # Check CPU
        # Find a cluster with available cores
        cluster_idx = None
        for i, available_cores in enumerate(self.resources['on_prem']['clusters']):
            if available_cores >= job.cpu_cores:
                cluster_idx = i
                break
        
        if cluster_idx is None:
            return 1 #'Insufficient CPU cores'
        
        
        # Check licenses
        for license in job.license:
            if self.get_available_licenses(license.license_name) < license.license_count:
                return 2 #'Insufficient licenses'
            
        # Set the cluster for the job
        job.run_cluster = cluster_idx
        
        return 0 #'Can schedule'
    

    def can_schedule_job_on_cloud(self, job: Job) -> int:
        """
        Check if a job can be scheduled on cloud based on available CPU cores.
        
        :param job: The job to be checked.
        :return: 0 if the job can be scheduled, 1 if insufficient CPU cores, 2 if insufficient licenses.
        """
        print(self.resources['cloud']['available_cores'], job.cpu_cores)
         # Check CPU cores
        if self.resources['cloud']['available_cores'] >= job.cpu_cores:
            for license in job.license:
                if self.get_available_licenses(license.license_name) < license.license_count:
                    return 2  # 'Insufficient licenses'
            return 0  # 'Can schedule'
        return 1  # 'Insufficient CPU cores'
    
    def allocate_resources_on_cloud(self, job: Job) -> bool:
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
    
    
    def allocate_resources(self, job: Job):
        """
        Allocate cores + licenses for job on-prem.
        Scheduler must set job.run_cluster.
        """
        cluster_idx = job.run_cluster
        if cluster_idx is None:
            return False
        
        if not self.allocate_cores(job.cpu_cores, cluster_idx):
            return False
        
        for license in job.license:
            if not self.allocate_license(license.license_name, license.license_count):
                self.release_cores(job.cpu_cores, cluster_idx)
                return False
        
        return True
        
    def release_resources(self, job, TwoPhase=False):
        """
        Release cores + licenses for job.
        Uses job.run_cluster to know where to free cores.
        """
        cluster_idx = job.run_cluster
        if cluster_idx is not None:
            self.release_cores(job.cpu_cores, cluster_idx)
        
        for license in job.license:
            self.release_license(license.license_name, license.license_count)
