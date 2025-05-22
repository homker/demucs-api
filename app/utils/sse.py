import json
import time
import threading
from flask import Response, stream_with_context
import logging

logger = logging.getLogger(__name__)

class SSEManager:
    """Server-Sent Events (SSE) Manager for tracking progress of long-running tasks"""
    
    def __init__(self):
        # Task progress storage: job_id -> progress info
        self.tasks = {}
        # Task lock to prevent race conditions
        self.lock = threading.Lock()
    
    def create_task(self, job_id):
        """Create a new task with initial progress"""
        with self.lock:
            self.tasks[job_id] = {
                'job_id': job_id,
                'progress': 0,
                'status': 'processing',
                'message': 'Task started',
                'started_at': time.time(),
                'last_update': time.time(),
                'result_file': None
            }
        return job_id
    
    def update_progress(self, job_id, progress, message=None, status=None, result_file=None):
        """Update the progress of a task"""
        with self.lock:
            if job_id not in self.tasks:
                return False
            
            task = self.tasks[job_id]
            task['progress'] = min(max(0, progress), 100)  # Ensure progress is between 0-100
            
            if message:
                task['message'] = message
            
            if status:
                task['status'] = status
                
            if result_file:
                task['result_file'] = result_file
                
            task['last_update'] = time.time()
            
            # If task is complete, update status
            if progress >= 100 and status != 'error':
                task['status'] = 'completed'
                if not message:
                    task['message'] = 'Task completed'
            
            return True
    
    def set_error(self, job_id, error_message):
        """Set task error status"""
        with self.lock:
            if job_id not in self.tasks:
                return False
            
            self.tasks[job_id]['status'] = 'error'
            self.tasks[job_id]['message'] = error_message
            self.tasks[job_id]['last_update'] = time.time()
            return True
    
    def get_progress(self, job_id):
        """Get current progress of a task"""
        with self.lock:
            if job_id not in self.tasks:
                return None
            return dict(self.tasks[job_id])
    
    def get_result_file(self, job_id):
        """Get result file path for a completed task"""
        with self.lock:
            if job_id not in self.tasks:
                return None
            
            task = self.tasks[job_id]
            if task['status'] != 'completed' or not task['result_file']:
                return None
                
            return task['result_file']
    
    def clean_task(self, job_id):
        """Remove a task from tracking"""
        with self.lock:
            if job_id in self.tasks:
                del self.tasks[job_id]
                return True
            return False
    
    def clean_old_tasks(self, max_age_seconds=3600):
        """Clean up tasks older than specified age"""
        now = time.time()
        with self.lock:
            for job_id in list(self.tasks.keys()):
                task = self.tasks[job_id]
                # Clean completed or error tasks after max_age_seconds
                if ((task['status'] in ['completed', 'error']) and 
                    (now - task['last_update'] > max_age_seconds)):
                    del self.tasks[job_id]
                    
    def stream_progress(self, job_id):
        """Generate SSE stream for a task's progress"""
        if job_id not in self.tasks:
            yield self._format_sse({"error": "Task not found"})
            return
            
        # Send initial progress
        yield self._format_sse(self.get_progress(job_id))
        
        # Continue sending updates until task completes or errors
        retry_count = 0
        max_retries = 5  # Stop after 5 failed checks
        
        while retry_count < max_retries:
            time.sleep(1)  # Check progress every second
            
            progress = self.get_progress(job_id)
            if not progress:
                retry_count += 1
                continue
                
            yield self._format_sse(progress)
            
            # If task is completed or failed, stop streaming
            if progress['status'] in ['completed', 'error']:
                break
                
        # Final message
        yield self._format_sse({"message": "Stream closed"})
    
    def _format_sse(self, data):
        """Format data as SSE message"""
        if isinstance(data, dict):
            data = json.dumps(data)
        return f"data: {data}\n\n"


def create_sse_response(generator_func):
    """Create a Server-Sent Events response"""
    return Response(
        stream_with_context(generator_func),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable buffering for Nginx
        }
    ) 