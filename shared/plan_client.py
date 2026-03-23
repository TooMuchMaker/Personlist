import requests
from typing import Dict, List, Optional
from datetime import datetime

PLAN_API_BASE = "http://127.0.0.1:5001"

class PlanClient:
    def __init__(self, source: str):
        self.source = source
        self.base_url = PLAN_API_BASE
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        url = f"{self.base_url}{endpoint}"
        try:
            if method == 'GET':
                response = requests.get(url, timeout=5, proxies={'http': None, 'https': None})
            elif method == 'POST':
                response = requests.post(url, json=data, timeout=5, proxies={'http': None, 'https': None})
            elif method == 'PUT':
                response = requests.put(url, json=data, timeout=5, proxies={'http': None, 'https': None})
            elif method == 'DELETE':
                response = requests.delete(url, timeout=5, proxies={'http': None, 'https': None})
            else:
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
            return None
        except:
            return None
    
    def is_connected(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/plans", timeout=2, proxies={'http': None, 'https': None})
            return response.status_code == 200
        except:
            return False
    
    def get_plans_by_source(self, sort_by: str = 'priority') -> List[Dict]:
        result = self._request('GET', f"/api/plans/source/{self.source}?sort={sort_by}")
        return result if isinstance(result, list) else []
    
    def get_plan_by_source_id(self, source_id: int) -> Optional[Dict]:
        return self._request('GET', f"/api/plans/source/{self.source}/{source_id}")
    
    def create_plan(self, title: str, plan_type: str = 'short_term', source_id: Optional[int] = None,
                    description: str = '', priority: str = 'medium', status: str = 'pending',
                    start_date: str = '', end_date: str = '', tags: List[str] = None,
                    progress: int = 0) -> Optional[Dict]:
        data = {
            'title': title,
            'plan_type': plan_type,
            'source': self.source,
            'source_id': source_id,
            'description': description,
            'priority': priority,
            'status': status,
            'start_date': start_date,
            'end_date': end_date,
            'tags': tags or [],
            'progress': progress
        }
        return self._request('POST', '/api/plans', data)
    
    def update_plan_by_source_id(self, source_id: int, **kwargs) -> Optional[Dict]:
        return self._request('PUT', f"/api/plans/source/{self.source}/{source_id}", kwargs)
    
    def delete_plan_by_source_id(self, source_id: int) -> Optional[Dict]:
        return self._request('DELETE', f"/api/plans/source/{self.source}/{source_id}")
    
    def update_status(self, source_id: int, status: str, progress: Optional[int] = None) -> Optional[Dict]:
        data = {'status': status}
        if progress is not None:
            data['progress'] = progress
        return self.update_plan_by_source_id(source_id, **data)
    
    def update_progress(self, source_id: int, progress: int) -> Optional[Dict]:
        return self.update_plan_by_source_id(source_id, progress=progress)
    
    def sync_plan(self, source_id: int, title: str, plan_type: str = 'short_term',
                  description: str = '', priority: str = 'medium', status: str = 'pending',
                  start_date: str = '', end_date: str = '', tags: List[str] = None,
                  progress: int = 0) -> Optional[Dict]:
        existing = self.get_plan_by_source_id(source_id)
        
        if existing:
            return self.update_plan_by_source_id(
                source_id,
                title=title,
                description=description,
                priority=priority,
                status=status,
                start_date=start_date,
                end_date=end_date,
                tags=tags or [],
                progress=progress
            )
        else:
            return self.create_plan(
                title=title,
                plan_type=plan_type,
                source_id=source_id,
                description=description,
                priority=priority,
                status=status,
                start_date=start_date,
                end_date=end_date,
                tags=tags,
                progress=progress
            )
