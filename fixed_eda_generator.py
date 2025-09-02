#!/usr/bin/env python3

"""
Fixed EDA License Contention Generator

Creates EDA workflows that respect license limits while still creating
meaningful contention for testing LATC algorithms.

Key fixes:
1. Respects total license consumption limits from config
2. Uses conservative license allocation per task
3. Creates contention through timing overlaps, not excessive license counts
4. Provides realistic license usage patterns

Usage:
python fixed_eda_generator.py mobile 10   # 10 concurrent mobile jobs
python fixed_eda_generator.py server 25   # 25 concurrent server jobs  
python fixed_eda_generator.py stress 40   # 40 jobs for stress testing
"""

import yaml
import random
import sys
from typing import Dict, List, Any

class RealisticEDAStages:
    """EDA stages with realistic license usage that respects limits"""
    
    def __init__(self):
        # Realistic license usage per task type
        self.stages = {
            # Front-end verification (moderate license usage)
            "rtl_sim": {
                "cpu": (4, 16), "time": (300, 1800),
                "licenses": ["synopsys_vcs", "cadence_xcelium", "mentor_questa"],
                "license_usage": (1, 2)  # 1-2 licenses per task
            },
            
            "lint_check": {
                "cpu": (2, 8), "time": (180, 900), 
                "licenses": ["synopsys_spyglass", "cadence_hal"],
                "license_usage": (1, 2)
            },
            
            "cdc_check": {
                "cpu": (2, 12), "time": (600, 2400),
                "licenses": ["synopsys_spyglass", "cadence_jaspergold"],
                "license_usage": (1, 3)
            },
            
            # Synthesis (critical path, moderate usage)
            "synthesis": {
                "cpu": (8, 32), "time": (900, 5400),
                "licenses": ["synopsys_dc", "cadence_genus"],
                "license_usage": (2, 4)  # Higher usage for synthesis
            },
            
            # DFT (specialized, conservative usage)
            "dft_insert": {
                "cpu": (4, 16), "time": (600, 3600),
                "licenses": ["synopsys_dft_compiler", "cadence_modus"],
                "license_usage": (1, 2)
            },
            
            # Physical design (CRITICAL - but realistic usage)
            "floorplan": {
                "cpu": (2, 8), "time": (1800, 7200),
                "licenses": ["synopsys_icc2", "cadence_innovus"],
                "license_usage": (1, 2)  # Conservative for floorplan
            },
            
            "powerplan": {
                "cpu": (2, 8), "time": (900, 3600),
                "licenses": ["synopsys_icc2", "cadence_innovus"],
                "license_usage": (1, 2)
            },
            
            "placement": {
                "cpu": (16, 48), "time": (3600, 14400),
                "licenses": ["synopsys_icc2", "cadence_innovus"],
                "license_usage": (2, 4)  # Higher usage for complex placement
            },
            
            "cts": {
                "cpu": (8, 24), "time": (1800, 7200),
                "licenses": ["synopsys_icc2", "cadence_innovus"],
                "license_usage": (1, 3)
            },
            
            "routing": {
                "cpu": (24, 64), "time": (5400, 21600),
                "licenses": ["synopsys_icc2", "cadence_innovus"],
                "license_usage": (2, 5)  # Highest P&R usage but still reasonable
            },
            
            # Analysis (moderate usage, longer duration)
            "timing": {
                "cpu": (4, 16), "time": (900, 5400),
                "licenses": ["synopsys_primetime", "cadence_tempus"],
                "license_usage": (1, 3)
            },
            
            "power": {
                "cpu": (4, 16), "time": (1800, 7200),
                "licenses": ["synopsys_primetime_px", "cadence_voltus"],
                "license_usage": (1, 2)  # Power analysis tools are scarce
            },
            
            "si_analysis": {
                "cpu": (6, 20), "time": (2400, 9600),
                "licenses": ["synopsys_primetime_si", "cadence_voltus_fi"],
                "license_usage": (1, 2)  # Very scarce tools, conservative usage
            },
            
            # Physical verification (long duration, moderate usage)
            "drc": {
                "cpu": (8, 32), "time": (3600, 14400),
                "licenses": ["mentor_calibre", "synopsys_icvalidator"],
                "license_usage": (2, 6)  # DRC can use multiple licenses for parallelization
            },
            
            "lvs": {
                "cpu": (4, 24), "time": (2400, 10800),
                "licenses": ["mentor_calibre", "synopsys_icvalidator"],
                "license_usage": (1, 4)
            },
            
            # Extraction (critical for signoff, moderate usage)
            "extraction": {
                "cpu": (8, 32), "time": (3600, 12000),
                "licenses": ["mentor_calibre_xrc", "synopsys_starrc"],
                "license_usage": (1, 3)  # Conservative extraction usage
            },
            
            # Formal verification (specialized, minimal usage)
            "formal_verify": {
                "cpu": (2, 12), "time": (1800, 10800),
                "licenses": ["cadence_conformal", "synopsys_formality"],
                "license_usage": (1, 2)  # Very specialized, minimal usage
            }
        }
        
        # Dependencies remain the same but create natural contention through timing
        self.flow_dependencies = {
            "rtl_sim": [],
            "lint_check": [],
            "cdc_check": ["rtl_sim"],
            "synthesis": ["rtl_sim", "lint_check"],
            "dft_insert": ["synthesis"],
            "floorplan": ["dft_insert"],
            "powerplan": ["dft_insert"],  # Can overlap with floorplan
            "placement": ["floorplan", "powerplan"],
            "cts": ["placement"],
            "routing": ["cts"],
            "timing": ["routing"],
            "power": ["routing"],       # Can overlap with timing
            "si_analysis": ["routing"], # Can overlap with timing + power
            "drc": ["routing"],         # Can overlap with analysis stages
            "lvs": ["routing"],         # Can overlap with DRC
            "extraction": ["drc", "lvs"],
            "formal_verify": ["synthesis", "extraction"]
        }

class FixedWorkflowGenerator:
    """Generates workflows that respect license limits"""
    
    def __init__(self, license_limits=None):
        self.stages = RealisticEDAStages()
        self.license_limits = license_limits or self.get_default_limits()
        self.complexity = {
            "mobile": {"scale": 0.7, "stages": 8},
            "server": {"scale": 1.0, "stages": 12}, 
            "gpu": {"scale": 1.3, "stages": 14},
            "stress": {"scale": 1.1, "stages": 13}
        }
    
    def get_default_limits(self):
        """Default realistic license limits"""
        return {
            "synopsys_dc": 35, "cadence_genus": 25,
            "synopsys_vcs": 80, "cadence_xcelium": 60, "mentor_questa": 45,
            "synopsys_icc2": 25, "cadence_innovus": 20,
            "synopsys_primetime": 35, "cadence_tempus": 25,
            "synopsys_primetime_px": 15, "synopsys_primetime_si": 8,
            "cadence_voltus": 12, "cadence_voltus_fi": 8,
            "synopsys_dft_compiler": 15, "cadence_modus": 12,
            "mentor_calibre": 30, "synopsys_icvalidator": 20,
            "mentor_calibre_xrc": 15, "synopsys_starrc": 12,
            "synopsys_spyglass": 20, "cadence_hal": 15,
            "cadence_jaspergold": 10, "cadence_conformal": 8,
            "synopsys_formality": 8
        }
    
    def generate_conservative_license_usage(self, stage_info, cpu_cores):
        """Generate license usage that respects global limits"""
        licenses = []
        if not stage_info["licenses"]:
            return licenses
        
        # Use realistic license counts based on stage type and CPU cores
        min_usage, max_usage = stage_info["license_usage"]
        
        # Scale license usage with CPU cores but keep it reasonable
        base_usage = min(max_usage, max(min_usage, cpu_cores // 8))
        license_count = random.randint(min_usage, min(max_usage, base_usage))
        
        # Choose one primary license type (realistic - most tasks use one tool)
        license_name = random.choice(stage_info["licenses"])
        licenses.append({
            "license_name": license_name,
            "license_count": license_count
        })
        
        # Occasionally add a second license type for comparison/backup
        if random.random() > 0.0001 and len(stage_info["licenses"]) > 1:
            secondary_license = random.choice([l for l in stage_info["licenses"] 
                                             if l != license_name])
            licenses.append({
                "license_name": secondary_license,
                "license_count": 1  # Just one backup license
            })
        
        return licenses
    
    def estimate_total_license_demand(self, workflow):
        """Estimate total license demand to check against limits"""
        license_demand = {}
        
        for job in workflow["jobs"]:
            for task in job["tasks"]:
                for license_req in task["licenses"]:
                    name = license_req["license_name"]
                    count = license_req["license_count"]
                    
                    if name not in license_demand:
                        license_demand[name] = 0
                    license_demand[name] += count
        
        return license_demand
    
    def validate_license_consumption(self, workflow):
        """Validate that total consumption doesn't exceed limits"""
        demand = self.estimate_total_license_demand(workflow)
        violations = []
        
        for license_name, total_demand in demand.items():
            limit = self.license_limits.get(license_name, 0)
            if total_demand > limit:
                violations.append({
                    "license": license_name,
                    "demand": total_demand,
                    "limit": limit,
                    "excess": total_demand - limit
                })
        
        return violations
    
    def generate_workflow(self, design_type="server", num_jobs=20):
        """Generate workflow with conservative license usage"""
        if design_type not in self.complexity:
            design_type = "server"
            
        scale = self.complexity[design_type]["scale"]
        max_stages = self.complexity[design_type]["stages"]
        
        workflow = {
            "workflow_name": f"realistic_contention_{design_type}_{num_jobs}jobs",
            "jobs": []
        }
        
        # Generate jobs with staggered submission to create realistic contention
        design_blocks = ["cpu_core", "gpu_block", "memory_ctrl", "io_subsystem",
                        "cache_ctrl", "pcie_ctrl", "dma_engine", "crypto_unit",
                        "network_block", "storage_ctrl"]
        
        for job_idx in range(num_jobs):
            block = design_blocks[job_idx % len(design_blocks)]
            
            # Staggered submission creates natural contention
            if job_idx < num_jobs // 3:
                # First third: rapid submission (peak contention)
                submit_time = job_idx * random.randint(30, 120)
            elif job_idx < 2 * num_jobs // 3:
                # Second third: moderate spacing
                base_time = (num_jobs // 3) * 120
                submit_time = base_time + (job_idx - num_jobs // 3) * random.randint(60, 300)
            else:
                # Final third: slower submission
                base_time = (2 * num_jobs // 3) * 300
                submit_time = base_time + (job_idx - 2 * num_jobs // 3) * random.randint(180, 600)
            
            # Realistic deadlines
            deadline_hours = {
                "mobile": 12, "server": 24, "gpu": 48, "stress": 36
            }.get(design_type, 24)
            deadline = deadline_hours * 3600
            
            job = {
                "job_id": f"job_{block}_{job_idx+1:03d}",
                "submit_time": submit_time,
                "deadline": deadline,
                "tasks": []
            }
            
            # Select stages for realistic flow coverage
            all_stages = list(self.stages.stages.keys())
            
            # Always include critical path stages
            critical_stages = ["synthesis", "placement", "routing", "timing"]
            selected_stages = critical_stages.copy()
            
            # Add random additional stages up to limit
            remaining_stages = [s for s in all_stages if s not in critical_stages]
            additional_count = min(max_stages - len(critical_stages), 
                                 len(remaining_stages))
            if additional_count > 0:
                selected_stages.extend(
                    random.sample(remaining_stages, 
                                random.randint(additional_count//2, additional_count))
                )
            
            # Order stages by dependencies
            ordered_stages = self.order_stages_by_dependencies(selected_stages)
            
            # Generate tasks with conservative license usage
            task_map = {}
            for stage_name in ordered_stages:
                stage_info = self.stages.stages[stage_name]
                
                # Scale resources conservatively
                cpu_min, cpu_max = stage_info["cpu"]
                cpu_cores = int(random.randint(cpu_min, cpu_max) * scale)
                cpu_cores = min(max(cpu_cores, 2), 64)  # Reasonable CPU limits
                
                time_min, time_max = stage_info["time"]
                duration = int(random.randint(time_min, time_max) * scale)
                
                # Conservative license usage
                licenses = self.generate_conservative_license_usage(stage_info, cpu_cores)
                
                # Dependencies
                depends_on = []
                for dep_stage in self.stages.flow_dependencies.get(stage_name, []):
                    if dep_stage in task_map:
                        depends_on.append(task_map[dep_stage])
                
                # Create task
                task_suffix = chr(ord('a') + len(job["tasks"]))
                task_id = f"task_{job_idx+1:03d}_{task_suffix}"
                
                task = {
                    "task_id": task_id,
                    "cpu_cores": cpu_cores,
                    "duration": duration,
                    "licenses": licenses,
                    "depends_on": depends_on
                }
                
                job["tasks"].append(task)
                task_map[stage_name] = task_id
            
            workflow["jobs"].append(job)
        
        return workflow
    
    def order_stages_by_dependencies(self, selected_stages):
        """Order stages respecting dependencies"""
        ordered = []
        remaining = selected_stages.copy()
        
        while remaining:
            ready = []
            for stage in remaining:
                deps = self.stages.flow_dependencies.get(stage, [])
                if all(dep in [s for s in selected_stages if s not in remaining] 
                      for dep in deps):
                    ready.append(stage)
            
            if not ready:
                ready = remaining  # Break cycles if any
            
            ordered.extend(ready)
            for stage in ready:
                remaining.remove(stage)
        
        return ordered
    
    def analyze_contention(self, workflow):
        """Analyze realistic contention patterns"""
        license_demand = self.estimate_total_license_demand(workflow)
        
        # Calculate utilization rates
        utilization = {}
        for license_name, demand in license_demand.items():
            limit = self.license_limits.get(license_name, 1)
            utilization[license_name] = (demand / limit) * 100
        
        # Find most contentious licenses
        contentious = sorted(utilization.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "total_jobs": len(workflow["jobs"]),
            "total_tasks": sum(len(job["tasks"]) for job in workflow["jobs"]),
            "license_demand": license_demand,
            "utilization": utilization,
            "most_contentious": contentious[:8],
            "submission_window": max(job["submit_time"] for job in workflow["jobs"]) / 60
        }

def main():
    if len(sys.argv) != 3:
        print("Usage: python fixed_eda_generator.py <design_type> <num_jobs>")
        print("Design types: mobile, server, gpu, stress")
        print("Recommended job counts: 10-40 for realistic testing")
        print("Example: python fixed_eda_generator.py server 25")
        sys.exit(1)
    
    design_type = sys.argv[1].lower()
    num_jobs = int(sys.argv[2])
    
    if design_type not in ["mobile", "server", "gpu", "stress"]:
        print(f"Invalid design type: {design_type}")
        print("Valid types: mobile, server, gpu, stress")
        sys.exit(1)
    
    generator = FixedWorkflowGenerator()
    workflow = generator.generate_workflow(design_type, num_jobs)
    
    # Validate license consumption
    violations = generator.validate_license_consumption(workflow)
    
    if violations:
        print(f"# WARNING: License limit violations detected!", file=sys.stderr)
        for violation in violations[:5]:  # Show top 5 violations
            print(f"# {violation['license']}: {violation['demand']} needed vs "
                 f"{violation['limit']} available (+{violation['excess']})", file=sys.stderr)
        print(f"# Consider reducing num_jobs or increasing license limits", file=sys.stderr)
    else:
        print(f"# ✅ All license consumption within limits", file=sys.stderr)
    
    # Output workflow
    yaml_output = yaml.dump(workflow, default_flow_style=False, indent=2, sort_keys=False)
    print(yaml_output)
    
    # Analysis
    stats = generator.analyze_contention(workflow)
    print(f"\n# CONTENTION ANALYSIS", file=sys.stderr)
    print(f"# Jobs: {stats['total_jobs']}, Tasks: {stats['total_tasks']}", file=sys.stderr)
    print(f"# Submission window: {stats['submission_window']:.1f} minutes", file=sys.stderr)
    print(f"# Top license utilization:", file=sys.stderr)
    
    for license_name, util_pct in stats['most_contentious'][:6]:
        demand = stats['license_demand'][license_name]
        print(f"# {license_name}: {demand} total ({util_pct:.1f}% utilization)", file=sys.stderr)

if __name__ == "__main__":
    main()