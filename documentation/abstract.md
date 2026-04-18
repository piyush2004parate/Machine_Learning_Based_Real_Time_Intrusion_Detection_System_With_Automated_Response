# ABSTRACT

The rapid escalation of automated, multi-vector cyber-attacks has necessitated the transition from traditional, rule-based security perimeters to intelligent, autonomous defense systems. This research presents **SecureWatch ML-IDS**, an advanced real-time Network Intrusion Detection and Response System designed to address the critical "False Positive Trap" prevalent in contemporary machine learning models. 

The core contribution of this work is the development of an **Asymmetric SMOTE-ENN** data engineering pipeline. By selectively oversampling minority threat classes from the **CSE-CIC-IDS2018** benchmark dataset while utilizing Edited Nearest Neighbors (ENN) to prune decision boundaries, the system achieves a state-of-the-art accuracy of **99.42%** with a focused **Top-20 feature subset**. 

Unlike passive monitoring tools, SecureWatch implements a **Hybrid Stateful-Ensemble Architecture** that couples a Random Forest classifier with a behavioral state tracker. This enables the detection of sophisticated threats such as slow port scanning and botnet heartbeats that evade traditional packet-level analysis. Furthermore, the system incorporates a low-latency **Bidirectional Mitigation Engine** capable of isolating confirmed attackers at the network layer in under **10 milliseconds**. 

Experimental results from live deployment demonstrate a consistent **3.4 ms inference latency**, proving the system's viability for high-speed enterprise environments. By bridging the gap between high-accuracy academic research and practical software engineering, this project provides a robust, scalable, and autonomous blueprint for the next generation of network security orchestration.

---

**Project Team:** *Piyush Parate, Chintan Parmar, Siddhesh Surve, Vashisht Urgonda*
