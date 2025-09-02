import heapq
import yaml
from simulator.job import Job
from simulator.task import Task
from simulator.license import License
from simulator.scheduler import Scheduler
from collections import defaultdict, deque


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
                    
                # # Aggregate licenses for the job from its tasks
                # license_dict = {}
                # for task in tasks:
                #     for lic in task.license:
                #         if lic.license_name in license_dict:
                #             license_dict[lic.license_name] += lic.license_count
                #         else:
                #             license_dict[lic.license_name] = lic.license_count
                # licenses = [License(name, count) for name, count in license_dict.items()]
                
                """
                The Final Solution
                Core Algorithm: License-Specific Subgraph + Dilworth's Theorem + Max Flow

                text
                For each license type L:
                1. Create subgraph GL containing ONLY nodes that use license L
                2. Preserve dependencies within the subgraph
                3. Apply Dilworth's theorem + Max Flow to find maximum antichain in GL  
                4. Sum up the license L usage from that antichain
                """
                # Calculate maximum concurrent license usage using Dilworth's theorem + Max Flow

                def calculate_max_concurrent_licenses(tasks):
                    """
                    Calculate maximum concurrent license usage for each license type using
                    license-specific subgraphs and Dilworth's theorem.
                    """
                    # Group tasks by license type
                    license_to_tasks = defaultdict(list)
                    for task in tasks:
                        for license in task.license:
                            license_to_tasks[license.license_name].append((task, license))
                    
                    max_concurrent_licenses = {}
                    
                    for license_name, task_license_pairs in license_to_tasks.items():
                        # Create subgraph for this license type
                        subgraph_tasks = [pair[0] for pair in task_license_pairs]
                        license_usage = {pair[0].task_id: pair[1].license_count for pair in task_license_pairs}
                        
                        # Build adjacency list for dependencies within subgraph
                        task_ids = {task.task_id for task in subgraph_tasks}
                        adj = defaultdict(list)
                        in_degree = defaultdict(int)
                        
                        # Build adjacency list including transitive dependencies
                        for task in subgraph_tasks:
                            in_degree[task.task_id] = 0
                        
                        # First, build the complete dependency graph for all tasks in the job
                        all_adj = defaultdict(list)
                        for task in tasks:  # Use all tasks, not just subgraph_tasks
                            for dep in task.depends_on:
                                all_adj[dep].append(task.task_id)
                        
                        # Find transitive dependencies between license-using tasks
                        def find_transitive_deps(start_task_id, target_task_ids):
                            """Find all tasks in target_task_ids that are transitively dependent on start_task_id"""
                            visited = set()
                            reachable = set()
                            
                            def dfs(task_id):
                                if task_id in visited:
                                    return
                                visited.add(task_id)
                                if task_id in target_task_ids and task_id != start_task_id:
                                    reachable.add(task_id)
                                for neighbor in all_adj[task_id]:
                                    dfs(neighbor)
                            
                            dfs(start_task_id)
                            return reachable
                        
                        # Build subgraph with transitive dependencies
                        for task in subgraph_tasks:
                            reachable_tasks = find_transitive_deps(task.task_id, task_ids)
                            for target_task_id in reachable_tasks:
                                adj[task.task_id].append(target_task_id)
                                in_degree[target_task_id] += 1
                        
                        # Transform the weighted graph into an unweighted graph
                        # Split each task node into multiple nodes based on license usage
                        def create_license_expanded_graph():
                            # Create mapping from original task_id to list of expanded node IDs
                            expanded_nodes = {}
                            expanded_adj = defaultdict(list)
                            expanded_in_degree = defaultdict(int)
                            
                            # Create expanded nodes
                            for task in subgraph_tasks:
                                task_id = task.task_id
                                license_count = license_usage[task_id]
                                # Create license_count nodes for this task
                                expanded_nodes[task_id] = [f"{task_id}_{i}" for i in range(license_count)]
                                
                                # Initialize in-degrees for expanded nodes
                                for expanded_node in expanded_nodes[task_id]:
                                    expanded_in_degree[expanded_node] = 0
                            
                            # Create edges between expanded nodes
                            for task_id in task_ids:
                                for neighbor_id in adj[task_id]:
                                    if neighbor_id in expanded_nodes:  # neighbor is in subgraph
                                        # Connect all expanded nodes of task_id to all expanded nodes of neighbor_id
                                        for src_node in expanded_nodes[task_id]:
                                            for dst_node in expanded_nodes[neighbor_id]:
                                                expanded_adj[src_node].append(dst_node)
                                                expanded_in_degree[dst_node] += 1
                            
                            return expanded_nodes, expanded_adj, expanded_in_degree
                        
                        # Apply max flow algorithm on expanded graph
                        def max_flow_expanded_bipartite(exp_adj, exp_in_degree):
                            all_expanded_nodes = list(set().union(*expanded_nodes.values()))
                            
                            # Build reachability matrix
                            reachable = defaultdict(set)
                            
                            # Use DFS or BFS to find all reachable pairs
                            def find_reachable(start):
                                visited = set()
                                stack = [start]
                                while stack:
                                    node = stack.pop()
                                    if node in visited:
                                        continue
                                    visited.add(node)
                                    reachable[start].add(node)
                                    for neighbor in exp_adj[node]:
                                        if neighbor not in visited:
                                            stack.append(neighbor)
                            
                            for node in all_expanded_nodes:
                                find_reachable(node)
                            
                            # Convert to bipartite matching problem
                            # Left set: all nodes, Right set: all nodes (duplicate)
                            # Edge exists if left node can reach right node (and they're different)
                            
                            match_left = {}
                            match_right = {}
                            
                            def find_augmenting_path(u, visited):
                                for v in all_expanded_nodes:
                                    if v != u and v in reachable[u] and v not in visited:
                                        visited.add(v)
                                        if v not in match_right or find_augmenting_path(match_right[v], visited):
                                            match_left[u] = v
                                            match_right[v] = u
                                            return True
                                return False
                            
                            # Find maximum matching
                            for u in all_expanded_nodes:
                                find_augmenting_path(u, set())
                            
                            matching_size = len(match_right)
                            
                            return matching_size, len(all_expanded_nodes)
                        
                        
                        if len(subgraph_tasks) == 0:
                            max_concurrent_licenses[license_name] = 0
                        else:
                            # Create expanded graph where each task is split by license usage
                            expanded_nodes, expanded_adj, expanded_in_degree = create_license_expanded_graph()
                            
                            # Apply Dilworth's theorem on expanded graph
                            max_matching, total_nodes = max_flow_expanded_bipartite(expanded_adj, expanded_in_degree)
                            max_antichain_size = total_nodes - max_matching
                            
                            # The maximum antichain size in the expanded graph directly gives us
                            # the maximum concurrent license usage
                            max_concurrent_licenses[license_name] = max_antichain_size
                    
                    return max_concurrent_licenses
                   
                # Calculate and create license objects
                max_concurrent = calculate_max_concurrent_licenses(tasks)
                licenses = [License(name, count) for name, count in max_concurrent.items()]
                

                
                NUM_CPU_CORES = 40  # Default CPU cores per job
                # Estimate total maximum CPU cores for a job by  sum up the cpus of each tasks at the same topological level
                if tasks:
                    max_parallel_tasks = 0
                    task_levels = {}
                    
                    def get_task_level(task_id, visited):
                        if task_id in visited:
                            return 0
                        visited.add(task_id)
                        task = next((t for t in tasks if t.task_id == task_id), None)
                        if not task or not task.depends_on:
                            return 0
                        level = 0
                        for dep in task.depends_on:
                            level = max(level, get_task_level(dep, visited) + 1)
                        return level    
                    
                    for task in tasks:
                        level = get_task_level(task.task_id, set())
                        if level in task_levels:
                            task_levels[level].append(task)
                        else:
                            task_levels[level] = [task]
                    max_parallel_tasks = max(max_parallel_tasks, max(task_levels.keys(), default=0))
                    for level, level_tasks in task_levels.items():
                        total_cpu = sum(t.cpu_cores for t in level_tasks)
                        max_parallel_tasks = max(max_parallel_tasks, total_cpu)
                    NUM_CPU_CORES = max_parallel_tasks
                    
                print(f"Estimated CPU cores for job {job_data['job_id']}: {NUM_CPU_CORES} based on max parallel tasks: {max_parallel_tasks}.")  #[Log]
                
                # Create Job object
                job = Job(
                    job_id=job_data['job_id'],
                    submit_time=job_data['submit_time'],
                    cpu_cores=NUM_CPU_CORES,
                    deadline=job_data['deadline'],
                    license=licenses,
                    tasks=tasks
                )
                jobs.append(job)
                

            for job in jobs:
                print(f"Loaded job: {job.job_id} with submit time {job.submit_time} and deadline {job.deadline}.")  #[Log]
                # print license requirements
                print(f"  License requirements: {[f'{lic.license_name}: {lic.license_count}' for lic in job.license]}")  #[Log]
                print(f"  Estimated CPU cores: {job.cpu_cores}")  #[Log]
            
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
    
    
        
        