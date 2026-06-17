import asyncio
import psutil
import torch
import threading
from typing import Dict, Optional, List, NamedTuple
from dataclasses import dataclass
from loguru import logger
from ..base_service import BaseService
from ...events.event_bus import EventBus

@dataclass
class ResourceRequirements:
    gpu_memory: Optional[int] = None  # MB
    cpu_cores: Optional[int] = None
    system_memory: Optional[int] = None  # MB
    priority: str = "normal"  # low, normal, high, critical

class GPUInfo(NamedTuple):
    device_id: int
    name: str
    total_memory: int
    available_memory: int
    utilization: float

class ResourceAllocation(NamedTuple):
    allocation_id: str
    gpu_devices: List[int]
    cpu_cores: List[int]
    memory_mb: int
    task_id: str

class ResourceManager(BaseService):
    """Enterprise Resource Manager for GPU/CPU/Memory allocation and optimization"""
    
    def __init__(self, event_bus: EventBus):
        super().__init__("ResourceManager")
        self.event_bus = event_bus
        self.gpu_pool = {}
        self.cpu_allocation = {}
        self.memory_allocation = {}
        self.active_allocations: Dict[str, ResourceAllocation] = {}
        self.allocation_lock = threading.Lock()
        self._monitoring = True
        
    async def _on_start(self):
        """Initialize resource pools and start monitoring"""
        await self._initialize_gpu_pool()
        await self._initialize_cpu_monitoring()
        await self._start_resource_monitoring()
        
        # Register event handlers
        await self.event_bus.subscribe("task.created", self._on_task_created)
        await self.event_bus.subscribe("task.completed", self._on_task_completed)
        
        logger.info(f"✅ Resource Manager initialized - GPUs: {len(self.gpu_pool)}, CPU cores: {psutil.cpu_count()}")
    
    async def _on_stop(self):
        """Clean shutdown with resource deallocation"""
        self._monitoring = False
        
        # Deallocate all resources
        with self.allocation_lock:
            for allocation in self.active_allocations.values():
                await self._deallocate_resources(allocation.allocation_id)
                
        logger.info("Resource Manager stopped - all resources deallocated")
    
    async def _initialize_gpu_pool(self):
        """Initialize GPU pool with memory tracking"""
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                self.gpu_pool[i] = {
                    'name': props.name,
                    'total_memory': props.total_memory // 1024 // 1024,  # MB
                    'allocated_memory': 0,
                    'reserved_tasks': [],
                    'utilization': 0.0
                }
            logger.info(f"GPU Pool initialized: {device_count} devices")
        else:
            logger.warning("No CUDA GPUs available")
    
    async def _initialize_cpu_monitoring(self):
        """Initialize CPU core allocation tracking"""
        total_cores = psutil.cpu_count()
        self.cpu_allocation = {
            'total_cores': total_cores,
            'allocated_cores': set(),
            'reservations': {}
        }
        logger.info(f"CPU monitoring initialized: {total_cores} cores")
    
    async def allocate_resources(self, task_id: str, requirements: ResourceRequirements) -> Optional[ResourceAllocation]:
        """Intelligent resource allocation based on requirements and availability"""
        with self.allocation_lock:
            try:
                allocation_id = f"{task_id}_{len(self.active_allocations)}"
                
                # GPU allocation
                allocated_gpus = []
                if requirements.gpu_memory:
                    allocated_gpus = await self._allocate_gpu_memory(requirements.gpu_memory, requirements.priority)
                    if not allocated_gpus and requirements.priority in ['high', 'critical']:
                        # Try to preempt lower priority tasks
                        allocated_gpus = await self._preempt_gpu_resources(requirements.gpu_memory)
                
                # CPU allocation
                allocated_cpus = []
                if requirements.cpu_cores:
                    allocated_cpus = await self._allocate_cpu_cores(requirements.cpu_cores)
                
                # Memory allocation
                allocated_memory = 0
                if requirements.system_memory:
                    allocated_memory = await self._allocate_system_memory(requirements.system_memory)
                
                # Create allocation record
                allocation = ResourceAllocation(
                    allocation_id=allocation_id,
                    gpu_devices=allocated_gpus,
                    cpu_cores=allocated_cpus,
                    memory_mb=allocated_memory,
                    task_id=task_id
                )
                
                self.active_allocations[allocation_id] = allocation
                
                # Emit allocation event
                await self.event_bus.emit("resources.allocated", {
                    "allocation_id": allocation_id,
                    "task_id": task_id,
                    "gpus": allocated_gpus,
                    "cpu_cores": len(allocated_cpus),
                    "memory_mb": allocated_memory
                })
                
                logger.info(f"Resources allocated for task {task_id}: GPUs {allocated_gpus}, CPUs {len(allocated_cpus)}, Memory {allocated_memory}MB")
                return allocation
                
            except Exception as e:
                logger.error(f"Failed to allocate resources for task {task_id}: {e}")
                return None
    
    async def _allocate_gpu_memory(self, required_memory: int, priority: str) -> List[int]:
        """Allocate GPU devices with sufficient memory"""
        allocated_devices = []
        
        for device_id, gpu_info in self.gpu_pool.items():
            available = gpu_info['total_memory'] - gpu_info['allocated_memory']
            if available >= required_memory:
                gpu_info['allocated_memory'] += required_memory
                allocated_devices.append(device_id)
                
                # Update GPU utilization
                utilization = gpu_info['allocated_memory'] / gpu_info['total_memory']
                gpu_info['utilization'] = utilization
                
                break
        
        return allocated_devices
    
    async def _allocate_cpu_cores(self, required_cores: int) -> List[int]:
        """Allocate CPU cores for computation"""
        available_cores = set(range(self.cpu_allocation['total_cores'])) - self.cpu_allocation['allocated_cores']
        
        if len(available_cores) >= required_cores:
            allocated = list(available_cores)[:required_cores]
            self.cpu_allocation['allocated_cores'].update(allocated)
            return allocated
        
        return []
    
    async def _allocate_system_memory(self, required_memory: int) -> int:
        """Allocate system memory with safety checks"""
        memory_info = psutil.virtual_memory()
        available_mb = memory_info.available // 1024 // 1024
        
        # Keep 20% safety margin
        safe_available = int(available_mb * 0.8)
        
        if safe_available >= required_memory:
            return required_memory
        
        logger.warning(f"Insufficient memory: requested {required_memory}MB, available {safe_available}MB")
        return 0
    
    async def deallocate_resources(self, allocation_id: str):
        """Deallocate resources and update availability"""
        with self.allocation_lock:
            await self._deallocate_resources(allocation_id)
    
    async def _deallocate_resources(self, allocation_id: str):
        """Internal deallocation logic"""
        if allocation_id not in self.active_allocations:
            return
        
        allocation = self.active_allocations[allocation_id]
        
        # Deallocate GPUs
        for gpu_id in allocation.gpu_devices:
            if gpu_id in self.gpu_pool:
                # Calculate released memory (simplified)
                self.gpu_pool[gpu_id]['allocated_memory'] = max(0, self.gpu_pool[gpu_id]['allocated_memory'] - allocation.memory_mb)
                self.gpu_pool[gpu_id]['utilization'] = self.gpu_pool[gpu_id]['allocated_memory'] / self.gpu_pool[gpu_id]['total_memory']
        
        # Deallocate CPUs
        self.cpu_allocation['allocated_cores'] -= set(allocation.cpu_cores)
        
        # Remove allocation
        del self.active_allocations[allocation_id]
        
        # Emit deallocation event
        await self.event_bus.emit("resources.deallocated", {
            "allocation_id": allocation_id,
            "task_id": allocation.task_id
        })
        
        logger.info(f"Resources deallocated for allocation {allocation_id}")
    
    async def _start_resource_monitoring(self):
        """Start background resource monitoring"""
        asyncio.create_task(self._monitor_resources())
    
    async def _monitor_resources(self):
        """Monitor resource utilization and emit metrics"""
        while self._monitoring:
            try:
                # GPU metrics
                gpu_metrics = []
                for device_id, gpu_info in self.gpu_pool.items():
                    if torch.cuda.is_available():
                        torch.cuda.synchronize(device_id)
                        memory_cached = torch.cuda.memory_cached(device_id) // 1024 // 1024
                        
                    gpu_metrics.append({
                        'device_id': device_id,
                        'utilization': gpu_info['utilization'],
                        'allocated_memory': gpu_info['allocated_memory'],
                        'total_memory': gpu_info['total_memory']
                    })
                
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                allocated_cores = len(self.cpu_allocation['allocated_cores'])
                
                # Memory metrics
                memory_info = psutil.virtual_memory()
                
                # Emit metrics event
                await self.event_bus.emit("metrics.resources", {
                    "gpu_metrics": gpu_metrics,
                    "cpu_utilization": cpu_percent,
                    "cpu_allocated_cores": allocated_cores,
                    "memory_percent": memory_info.percent,
                    "memory_available_mb": memory_info.available // 1024 // 1024,
                    "active_allocations": len(self.active_allocations)
                })
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
            
            await asyncio.sleep(5)  # Monitor every 5 seconds
    
    async def get_resource_status(self) -> Dict:
        """Get current resource utilization status"""
        gpu_status = []
        for device_id, gpu_info in self.gpu_pool.items():
            gpu_status.append(GPUInfo(
                device_id=device_id,
                name=gpu_info['name'],
                total_memory=gpu_info['total_memory'],
                available_memory=gpu_info['total_memory'] - gpu_info['allocated_memory'],
                utilization=gpu_info['utilization']
            ))
        
        memory_info = psutil.virtual_memory()
        
        return {
            "gpus": gpu_status,
            "cpu_cores_total": self.cpu_allocation['total_cores'],
            "cpu_cores_allocated": len(self.cpu_allocation['allocated_cores']),
            "memory_total_mb": memory_info.total // 1024 // 1024,
            "memory_available_mb": memory_info.available // 1024 // 1024,
            "active_allocations": len(self.active_allocations)
        }
    
    async def _on_task_created(self, event_data: dict):
        """Handle task creation events"""
        task_id = event_data.get('task_id')
        requirements = event_data.get('resource_requirements')
        
        if requirements:
            req = ResourceRequirements(**requirements)
            allocation = await self.allocate_resources(task_id, req)
            
            if not allocation:
                await self.event_bus.emit("task.resource_allocation_failed", {
                    "task_id": task_id,
                    "reason": "insufficient_resources"
                })
    
    async def _on_task_completed(self, event_data: dict):
        """Handle task completion events"""
        task_id = event_data.get('task_id')
        
        # Find and deallocate resources for this task
        for allocation_id, allocation in self.active_allocations.items():
            if allocation.task_id == task_id:
                await self.deallocate_resources(allocation_id)
                break
    
    async def _preempt_gpu_resources(self, required_memory: int) -> List[int]:
        """Preempt lower priority tasks to free GPU memory"""
        # Implementation for preempting lower priority tasks
        # This would involve checking current task priorities and stopping lower priority ones
        logger.info(f"Attempting to preempt GPU resources for {required_memory}MB")
        return []  # Simplified for now
