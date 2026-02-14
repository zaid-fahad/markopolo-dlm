import requests
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

class DistributedLock:
    def __init__(self, nodes):
        self.nodes = nodes
        self.client_id = str(uuid.uuid4())
        self.clock_drift_buffer = 0.5 # 500ms safety buffer

    def acquire(self, lock_name, ttl=5.0):
        start_time = time.monotonic()
        votes = []
        
        with ThreadPoolExecutor(max_workers=len(self.nodes)) as ex:
            futures = [ex.submit(self._hit_node, n, lock_name, ttl) for n in self.nodes]
            for f in futures:
                res = f.result()
                if res: votes.append(res)

        # Quorum (N/2 + 1)
        if len(votes) >= (len(self.nodes) // 2 + 1):
            elapsed = time.monotonic() - start_time
            validity = ttl - elapsed - self.clock_drift_buffer
            
            if validity > 0:
                return {
                    "token": max(v['token'] for v in votes),
                    "validity": validity,
                    "votes": votes
                    }
        
        self.release(lock_name, votes) # Rollback partial grants
        return None

    def _hit_node(self, node, name, ttl):
        try:
            r = requests.post(f"{node}/acquire", json={"name": name, "client_id": self.client_id, "ttl": ttl}, timeout=0.1)
            return {"node": node, "token": r.json()['token']} if r.status_code == 200 else None
        except: return None

    def release(self, lock_name, votes):
        for v in votes:
            try: requests.post(f"{v['node']}/release", json={"name": lock_name, "client_id": self.client_id, "token": v['token']}, timeout=0.1)
            except: pass