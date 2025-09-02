from simulator.task import Task
from simulator.license import License
# from simulator.scheduler import Scheduler
from collections import defaultdict, deque

class Job:
    def __init__(self, job_id: int, submit_time: int, cpu_cores: int, deadline: int, license: list[License], tasks: list[Task]):
        """
        Initializes a Job instance with the given parameters.
        """
        
        # Static attributes
        self.job_id = job_id
        self.submit_time = submit_time
        self.cpu_cores = cpu_cores
        self.using_cpu_cores = 0
        self.deadline = deadline
        self.license = license
        self.tasks: list[Task] = tasks
        
        # Runtime attributes
        self.run_cluster = None
        self.start_time = None
        self.end_time = None
        self.status = "pending"  # or "running", "completed", "missed_deadline"
        self.where = None # "on-prem" or "cloud"
    
    def __lt__(self, other):
        """
        Less than comparison for priority queue ordering.
        Primary: submit_time (earlier jobs have higher priority)
        Secondary: job_id (for deterministic ordering when submit_times are equal)
        """
        if self.submit_time != other.submit_time:
            return self.submit_time < other.submit_time
        return self.job_id < other.job_id
    
    def calculate_max_concurrent_licenses(self, tasks):
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
            def max_matching_expanded_bipartite(exp_adj, exp_in_degree):
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
                max_matching, total_nodes = max_matching_expanded_bipartite(expanded_adj, expanded_in_degree)
                max_antichain_size = total_nodes - max_matching
                
                # The maximum antichain size in the expanded graph directly gives us
                # the maximum concurrent license usage
                max_concurrent_licenses[license_name] = max_antichain_size
        
        return max_concurrent_licenses

    
    # Task Level Functions
    def ready_tasks(self) -> list[Task]:
        completed = {t.task_id for t in self.tasks if t.status == "completed"}
        return [t for t in self.tasks if t.status == "pending" and t.is_ready(completed)]
    
    def run(self, current_time, scheduler=None, TwoPhase=False):
        if self.status != "running":
            return

        # 1) advance running tasks
        for task in self.tasks:
            if task.status == "running":
                if task.start_time + task.duration <= current_time:
                    task.status = "completed"
                    self.cpu_cores += task.cpu_cores  # return cores to job's pool
                    self.using_cpu_cores -= task.cpu_cores
                    print(f"Task {task.task_id} of Job {self.job_id} completed task at time {current_time}.")
                    
                    if TwoPhase and scheduler.type == "Standard":
                        print(f"Releasing licenses for Task {task.task_id} of Job {self.job_id}.") #[Log]
                        for lic in task.license:
                            scheduler.resource_manager.release_license(lic.license_name, lic.license_count)
                            # Also reduce the license in the job's license requirement
                            for job_lic in self.license:
                                if job_lic.license_name == lic.license_name:
                                    job_lic.license_count -= lic.license_count
                                    break
                            print(f"Released {lic.license_count} licenses of type {lic.license_name}")
                                
                    elif TwoPhase and scheduler.type == "LATC":
                        print(f"Releasing licenses for Task {task.task_id} of Job {self.job_id}.") #[Log]
                        
                        # For each license type used by the task, we re-evaluate the need
                        # Get remaining tasks in the DAG
                        remaining_tasks = [t for t in self.tasks if t.status != "completed"]
                        # Re-evaluate license requirements for remaining tasks
                        max_concurrent = self.calculate_max_concurrent_licenses(remaining_tasks)
                        
                        for lic in task.license:
                            print (f"Re-evaluating license type {lic.license_name} after completing Task {task.task_id}.") #[Log]
                            print (f"Max concurrent needed: {max_concurrent.get(lic.license_name, 0)}") #[Log]
                            print (f"Current reserved: {[l for l in self.license if l.license_name == lic.license_name][0].license_count}") #[Log]
                            
                            # Check if we can release any licenses for this license type
                            current_reserve = [l for l in self.license if l.license_name == lic.license_name][0].license_count
                            re_eval_result = max_concurrent.get(lic.license_name, 0)
                        

                            if current_reserve > re_eval_result:
                                print (""f"Releasing licenses based on re-evaluation...") #[Log]
                                release_amount = current_reserve - re_eval_result
                                scheduler.resource_manager.release_license(lic.license_name, release_amount)
                                # Also reduce the license in the job's license requirement
                                for job_lic in self.license:
                                    if job_lic.license_name == lic.license_name:
                                        job_lic.license_count -= release_amount
                                        break
                                print(f"Released {release_amount} licenses of type {lic.license_name} after re-evaluation")
                            
                    else:
                        pass
                else:
                    # print(f"Task {task.task_id} of Job {self.job_id} is still running.") #[Log]
                    pass
                    
        # 2) start ready tasks
        # print(f"Job {self.job_id} at time {current_time}: trying to start ready tasks. Using cores: {self.using_cpu_cores}/{self.cpu_cores}") #[Log]
        # print(f"Ready tasks: {[t.task_id for t in self.ready_tasks()]}") #[Log]
        
        for task in self.ready_tasks():
            if self.cpu_cores >= task.cpu_cores:
                task.status = "running"
                self.cpu_cores -= task.cpu_cores
                self.using_cpu_cores += task.cpu_cores
                task.start(current_time)
    
    def all_completed(self):
        return all(t.status == "completed" for t in self.tasks)
        
    
    # Job Level Functions

    def start(self, start_time, where="on-prem"):
        self.start_time = start_time
        self.status = "running"
        self.where = where
    
    def complete(self, end_time):
        self.end_time = end_time
        self.status = "completed"
        
    def is_completed(self):
        return self.status == "completed"
    
        
    def update_status(self, current_time):
        if ((self.status == "pending") and current_time >= self.deadline):
            self.status = "missed_deadline"
        
    def __repr__(self):
        return (f"Job(job_id={self.job_id}, submit_time={self.submit_time}, "
                f"cpu_cores={self.cpu_cores}, "
                f"deadline={self.deadline}, license={self.license}, "
                f"start_time={self.start_time}, end_time={self.end_time}, "
                f"status={self.status})")
        