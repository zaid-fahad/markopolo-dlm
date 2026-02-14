import subprocess
from client import DistributedLock

NODES = ["http://localhost:5001", "http://localhost:5002", "http://localhost:5003"]

def run_test(name, func):
    print(f"\n Starting Test: {name}")
    try: 
        func()
        print(f"PASSED: {name}")
    except Exception as e: 
        print(f"FAILED: {name} | Error: {e}")

def test_mutual_exclusion():
    c1, c2 = DistributedLock(NODES), DistributedLock(NODES)
    l1 = c1.acquire("test_lock", ttl=10)
    assert l1 is not None, "Client 1 failed to acquire"
    l2 = c2.acquire("test_lock", ttl=10)
    assert l2 is None, "Client 2 acquired a lock held by Client 1!"

def test_fault_tolerance():
    print("Simulating node crash (killing node3 container)...")
    subprocess.run(["docker", "stop", "markopolo-node3-1"], capture_output=True)
    
    c1 = DistributedLock(NODES)
    l1 = c1.acquire("res_fault", ttl=5)
    assert l1 is not None, "Failed to reach quorum with 1 node down"
    
    subprocess.run(["docker", "start", "markopolo-node3-1"], capture_output=True)

if __name__ == "__main__":
    run_test("Mutual Exclusion", test_mutual_exclusion)
    run_test("Fault Tolerance (1/3 nodes dead)", test_fault_tolerance)