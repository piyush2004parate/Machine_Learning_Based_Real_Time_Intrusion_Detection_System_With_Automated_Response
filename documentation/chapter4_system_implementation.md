# CHAPTER 4: SYSTEM IMPLEMENTATION

---

## 4.1 Development Environment and Technology Stack

The SecureWatch ML-IDS is architected as a full-stack, distributed real-time application. Unlike traditional request-response systems, this project utilizes high-concurrency technologies to handle the velocity of network traffic.

### 4.1.1 Core Backend Stack
-   **Django & Django Channels (v4.2):** Chosen as the central orchestrator. Django Channels enables the use of **WebSockets**, allowing the server to push traffic data to the UI instantly without the client needing to poll the server.
-   **Scapy (v2.5.0):** Integrated for low-level packet sniffing and 5-tuple aggregation. Scapy provides a Pythonic wrapper over `libpcap`, making it suitable for granular packet inspection.
-   **Machine Learning Engine:** Built with **Scikit-Learn**. The Random Forest model is serialized into a `joblib` file for efficient memory-mapped loading at system runtime.

### 4.1.2 Frontend & UI Stack
-   **React.js & Tailwind CSS:** Used to build a "Single Page Application" (SPA) dashboard. React's state management ensures that the "Live Feed" component re-renders efficiently as packets arrive over the WebSocket.
-   **Lucide-React & Recharts:** Providing high-fidelity icons and real-time charting for the threat intelligence dashboard.

---

## 4.2 Module-Wise Implementation

### 4.2.1 Real-Time Packet Analysis Module
Implemented within the **Real-time Processing Module**, this component acts as the "Nerve Center." It initializes an asynchronous packet sniffer that captures traffic from the specified Network Interface Card (NIC).
-   **Logic:** As packets arrive, the sniffer aggregates them into flow vectors. Any packet whose source or destination IP matches the internal blocked inventory list is discarded before reaching the classification stage.

### 4.2.2 Automated Response Engine
Implemented within the **Response Logic Layer**, this submodule translates an ML "Alert" into a physical network rule. 
-   **Execution:** The engine makes dynamic shell calls to the host network configuration API. It creates a high-priority "Block" rule for the attacker's IP.
-   **Isolation:** To prevent the IDS host from leaking defensive responses, the engine applies Inbound and Outbound rules simultaneously.

---

## 4.3 Key Logic and Sequence Analysis

### 4.3.1 Data Flow Sequence (Figure 4.1)
The following high-resolution technical diagram illustrates the sub-second transition of a network packet from the wire to the user dashboard.

![Real-Time Data Pipeline](/C:/Users/sanja/.gemini/antigravity/brain/ebe9bc43-24a3-4363-a74e-d657221af2a5/realtime_pipeline_diagram_1776175112422.png)

*Figure 4.1: High-fidelity Sequence Diagram showing the 5-stage packet classification pipeline.*

### 4.3.2 Bidirectional Mitigation Flow (Figure 4.2)
The following diagram defines the decision-making process for the automated response layer, highlighting the bidirectional isolation strategy.

![Automated Mitigation Logic](/C:/Users/sanja/.gemini/antigravity/brain/ebe9bc43-24a3-4363-a74e-d657221af2a5/mitigation_logic_diagram_v2_1776177900208.png)

*Figure 4.2: Technical flowchart of the Automated Mitigation Engine and Firewall Action layer.*

---

## 4.4 Software Engineering Challenges and Solutions

During the implementation phase, three significant challenges were identified and successfully resolved:

### 1. The "Dashboard Sticking" Challenge
**Problem:** During high-volume attacks (e.g., Nmap scans), the backend would sniff thousands of packets per second. The WebSocket would attempt to push every packet to the frontend, resulting in a "buffer bloat" situation where the browser UI would freeze or lag behind the actual attack by several minutes.
**Solution:** A **Memory Buffer Cap** was implemented within the real-time processing module. The live traffic queue was restricted to **100 packets**. If the queue exceeds this limit, old packets are dropped at the backend level, ensuring the frontend always displays current "Live" traffic.

### 2. The "Defensive Response Leak" Challenge
**Problem:** Blocking an attacker's Inbound packets only solves half the problem. The host operating system would still attempt to send TCP Resets or ACKs back to the attacker. These "leaks" cluttered the dashboard logs and alerted the attacker to the existence of an active security system.
**Solution:** Advanced **Bidirectional Mitigation** was developed. The block action was upgraded to apply both Inbound and Outbound firewall rules, completely isolating the host-attacker communication channel.

### 3. Asymmetric Dataset Noise
**Problem:** Initial training with standard SMOTE created "fake" packets that overlapped with benign traffic, leading to false positives.
**Solution:** Implementation of the **Asymmetric SMOTE-ENN Pipeline**. We used Edited Nearest Neighbours to "prune" the decision boundaries, resulting in a significantly cleaner model that does not flag legitimate network chatter as anomalous.

---

## 4.5 Deployment and Configuration

The implementation requires a specific "Production Mode" setup:
-   **Administrative Access:** The Django backend must be run with **Run as Administrator** privileges to allow Python to manipulate the Windows Firewall API.
-   **Promiscuous Mode:** The network card must be configured for promiscuous mode via Scapy's `conf.iface` to capture traffic not specifically addressed to the host machine.
