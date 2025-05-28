class ResourceManager:
    def __init__(self, config):
        
        self.resources = {}
        self.licenses = {}

    def get_available_cores(self):
        """
        Returns the number of available CPU cores for a job.
        """
        return sum(resource['available_cores'] for resource in self.resources.values())
    
    def allocate_cores(self, required_cores):
        """
        Allocates CPU cores for a job if available.
        Returns True if allocation is successful, False otherwise.
        """
        for resource in self.resources.values():
            if resource['available_cores'] >= required_cores:
                resource['available_cores'] -= required_cores
                return True
        return False
    
    def release_cores(self, cores):
        """
        Releases allocated CPU cores back to the resource pool.
        """
        for resource in self.resources.values():
            resource['available_cores'] += cores
            return
    
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
        
        
        
        
    

    