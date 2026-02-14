# Chaos-Proof Distributed Lock Manager (DLM)

A lightweight, quorum-based distributed lock manager built from scratch to coordinate access to shared resources without a centralized coordinator. This system is designed to maintain **Mutual Exclusion** even in the face of network partitions, node crashes, and clock skew.

---

## 🏗 Architecture Diagram

```mermaid
        [ Client Application ]
          /        |        \
        (Quorum Request: 2/3 Nodes)
      /            |            \
[Node 1:5001]   [Node 2:5002]    [Node 3:5003]
(SQLite State)  (SQLite State)  (SQLite State)
      |            |            |
      +--- Monotonic Clock Sync ---+

```

---

## 🛠 How It Works: Quorum-Lease Algorithm

* **Quorum Voting**: The client broadcasts an `acquire` request to all available nodes. It must receive a **"GRANTED"** response from a majority () to successfully hold the lock.
* **Monotonic TTL**: Servers use `time.monotonic()` to track lock expiry. This ensures the lease duration is measured by hardware ticks rather than "Time of Day," preventing issues where system clocks are adjusted manually or via NTP.
* **Pessimistic Validity**: The client calculates its own lease duration by subtracting the network round-trip time and a safety **Drift Buffer** (500ms) from the TTL.
* **Fencing Tokens**: Every lock grant includes a unique, incrementing token. Clients must present this token for all operations, ensuring "zombie" clients with expired leases are rejected by the backend resources.

---

## Trade-offs

* **Consistency over Availability**: Following the **CAP theorem**, this system prioritizes Consistency. If a majority of nodes are down, the system stops granting new locks to prevent potential data corruption.
* **Latency vs. Safety**: A 500ms "safety gap" is introduced. This means a lock might be unusable by the client slightly before it is technically expired on the server, ensuring no two clients overlap during clock drift.

---

##  Known Limitations

* **Small Cluster Optimization**: While highly resilient, the broadcast nature of the quorum is designed for 3, 5, or 7-node clusters rather than large-scale data center distribution.
* **Poll-based Library**: The current client library handles retries via polling rather than a persistent "wait/notify" queue.

---

##  How to Run

### 1. Start the Cluster

Spin up the 3-node distributed environment using Docker Compose:

```bash
docker-compose up --build -d

```

### 2. Install Library Dependencies

Ensure you have the necessary Python packages installed locally:

```bash
pip install -r requirements.txt

```



---
