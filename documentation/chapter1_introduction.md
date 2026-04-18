# From KNN to Ensemble Learning: Advancing Real-Time Network Intrusion Detection with Asymmetric SMOTE-ENN Balancing on the CSE-CIC-IDS2018 Benchmark

---

# CHAPTER 1: INTRODUCTION

---

## 1.1 Overview

The discipline of network security has undergone a fundamental evolution over the past decade, driven by the exponential growth in the volume, velocity, and sophistication of cyber threats targeting enterprise networks. Modern enterprise environments are subject to an increasingly complex and dynamic threat landscape, ranging from high-volume volumetric attacks such as Distributed Denial-of-Service (DDoS), which can saturate bandwidth within seconds, to subtle long-term infiltration campaigns that may persist within a network for weeks without detection. As organizations grow their digital footprint, the traffic volumes traversing their internal networks have grown beyond the capacity of any manual inspection process, necessitating intelligent, automated monitoring systems.

Traditional approaches to network security, particularly **rule-based Intrusion Detection Systems (IDS)** such as Snort and Suricata, rely on pre-defined signature databases to identify known malicious patterns. While effective against previously catalogued attack vectors, such systems are fundamentally incapable of generalizing to novel or obfuscated variants of known threats. Their performance degrades rapidly in real-world environments where attackers continuously evolve their tactics to evade signature lookups. Furthermore, the high administrative overhead required to maintain and update signature databases renders them impractical at scale.

In response to these limitations, there has been a growing academic and industrial interest in **Machine Learning-based Intrusion Detection Systems (ML-IDS)**. These systems operate by learning the behavioral signatures of malicious network flows directly from labeled training data, enabling generalization to unseen threat variants. Supervised classifiers, including K-Nearest Neighbors (KNN), Decision Trees, and ensemble techniques such as Random Forest, have demonstrated considerable promise over traditional rule-based methods when evaluated on industry-standard benchmark datasets.

The present project advances this field by systematically transitioning from a standard **K-Nearest Neighbors (KNN)** baseline to a more robust **Ensemble Learning** framework, evaluated rigorously on the enterprise-grade **CSE-CIC-IDS2018** benchmark dataset. A key methodological contribution is the introduction of an **Asymmetric SMOTE-ENN** data balancing pipeline, which addresses the critical class imbalance inherent to real-world network traffic without inducing the False Positive Trap associated with conventional oversampling techniques. The resulting champion model is deployed within a real-time inference backend, providing sub-5 ms classification latency and autonomous threat mitigation through firewall-based isolation, establishing a complete, production-ready Network Intrusion Detection System.

---

## 1.2 Motivation and Background

The increasing sophistication and frequency of cyberattacks against enterprise infrastructure present a critical research challenge. DDoS and Botnet attacks have grown significantly more automated, exploiting network protocol properties to bypass threshold-based detection mechanisms. Anomalies in high-throughput enterprise network traffic are highly transient and dynamic, rendering static signature-based IDS systems incapable of detecting new variants or low-rate probe attacks in real time.

A central technical challenge in deploying ML-based IDS solutions is the problem of **class imbalance**. In real-world enterprise network traffic, the Benign traffic class dominates the distribution by several orders of magnitude. In the CSE-CIC-IDS2018 dataset, for example, the Web Attack class constitutes only 53 natural instances out of nearly 16 million flow records, representing less than 0.001% of all observations. Standard data balancing techniques, such as Synthetic Minority Oversampling Technique (SMOTE), applied indiscriminately to all minority classes, can produce hundreds of thousands of synthetic samples for such extreme minorities, introducing significant distortions into the feature space. This phenomenon, referred to as the **False Positive Trap**, causes distance-based classifiers such as KNN to experience a significant degradation in Benign-class recall, dropping it to approximately 72%, and generating tens of thousands of false positives per inference cycle.

This project is motivated by the need to resolve these challenges through three primary innovations:

1.  **Dataset Upgrade**: Migration from the controlled laboratory UNSW-NB15 dataset to the enterprise-grade **CSE-CIC-IDS2018** benchmark, which captures seven authentic attack types under real-world class asymmetry conditions.
2.  **Asymmetric SMOTE-ENN Balancing**: A novel, class-aware resampling pipeline that respects the natural statistical distribution of traffic while ensuring adequate coverage of extreme minority attack classes using Edited Nearest Neighbours (ENN) as a post-processing boundary cleaner.
3.  **Automated Response Integration**: A fully autonomous mitigation layer using Windows Advanced Firewall API calls, triggered by real-time ML inference, providing sub-second response latency.

---

## 1.3 Objectives

The primary objectives of this project are as follows:

-   To design and implement a **Hybrid Intrusion Detection System** that combines ML-based anomaly detection with real-time Stateful Behavioral Analysis for multi-vector attack identification.
-   To train a **Champion Ensemble Model** on the CSE-CIC-IDS2018 dataset using a scientifically rigorous **Asymmetric SMOTE-ENN** preprocessing pipeline that preserves real-world class asymmetry.
-   To perform **Gini Impurity-based Feature Selection** using a Random Forest estimator, reducing the 78-dimensional CICFlowMeter feature space to the top 20 most informative attributes, achieving a 74.4% dimensional reduction.
-   To implement a **Real-Time Packet Sniffing Engine** using Scapy capable of extracting CIC-IDS2018 flow-level features on a per-packet basis with a classification latency of under 4 ms per flow.
-   To implement a **Stateful Behavioral Tracker** capable of independently identifying Port Scanning (≥ 4 unique destination ports per second), SSH/FTP Brute-force (≥ 5 login attempts with focused port targeting), and volumetric DoS floods.
-   To build an **Automated Response Engine** that executes Bidirectional Windows Firewall Isolation for detected threats, ensuring complete elimination of both inbound attacks and outbound defensive responses.
-   To develop a **Real-Time Web Dashboard** using React.js and Django Channels (WebSockets) for live traffic visualization, incident logging, and response management.
-   To validate the system's performance through empirical evaluation, reporting Overall Accuracy, Macro-Precision, Macro-Recall, F1-Score, and False Positive Rate (FPR) on an isolated, organic 20% test set.

---

## 1.4 Organization of the Report

This report is structured into multiple chapters to systematically present the proposed work.

**Chapter 1** introduces the topic, providing an overview, motivation and background, and objectives of the project.

**Chapter 2** presents a comprehensive literature survey of existing intrusion detection systems and highlights their limitations and research gaps.

**Chapter 3** describes the proposed methodology, including the Asymmetric SMOTE-ENN data engineering pipeline, the Champion Model Selection Framework, and the hardware/software requirements.

**Chapter 4** describes the practical implementation of the backend (Django Channels, Scapy), the frontend real-time dashboard (React.js), and the integration of the ML inference engine.

**Chapter 5** discusses the experimental results, including the Confusion Matrix, Classification Report, and performance analysis.

**Chapter 6** concludes the work and outlines future scope for further improvements and research directions.

---

## 1.5 Time Plan

The project was executed across a structured timeline of twelve months, divided into two academic semesters, each comprising six months of progressive development.

### Semester 1: Baseline Development and Gap Analysis

| Month | Activity |
| :--- | :--- |
| **Month 1** | Initial Project Formulation and Literature Survey on standard ML-IDS architectures |
| **Month 2** | Environment Setup and Baseline Dataset Acquisition (UNSW-NB15) |
| **Month 3** | Baseline Model Training (Standard KNN) and traditional feature extraction |
| **Month 4** | Initial Evaluation and Testing of the UNSW-NB15 model |
| **Month 5** | Gap Analysis — identifying the model's struggle with modern internet threats and the False Positive Trap |
| **Month 6** | Semester 1 Presentation, pivoting strategy, and finalizing the architecture for the Asymmetric SMOTE-ENN pipeline |

The first semester established the foundational research baseline. The project commenced with a comprehensive literature survey of existing ML-based IDS architectures, followed by the acquisition of the UNSW-NB15 dataset and the training of a standard K-Nearest Neighbors classifier using conventional feature extraction techniques. Initial evaluation revealed significant deficiencies in the baseline model's performance on real-world class distributions. A formal Gap Analysis conducted in Month 5 identified two critical limitations: the model's inability to generalize against modern enterprise-grade threats not well-represented in laboratory datasets, and the systematic False Positive Trap caused by unrestricted SMOTE oversampling. Month 6 concluded the semester with the presentation of these findings and the formalization of a pivoting strategy towards the CSE-CIC-IDS2018 dataset and the Asymmetric SMOTE-ENN pipeline.

---

### Semester 2: Advanced Pipeline and Real-Time Integration

| Month | Activity |
| :--- | :--- |
| **Month 7** | Dataset transition to CSE-CIC-IDS2018 and Advanced Exploration |
| **Month 8** | Data Preprocessing and Asymmetric SMOTE-ENN Pipeline Development |
| **Month 9** | Model Training, Champion Selection (Optimized KNN), and Gini-based Feature Engineering |
| **Month 10** | Backend Development (Django Channels, WebSocket, Scapy sniffer) for real-time latency under 5 ms |
| **Month 11** | Frontend Dashboard Development and Full System Integration |
| **Month 12** | Rigorous System Testing, Validation, Final Blackbook Reporting, and Documentation |

The second semester constituted the core engineering and research contribution of the project. Month 7 began with the transition to the enterprise-grade CSE-CIC-IDS2018 dataset, followed by in-depth exploratory data analysis of its class distribution across seven attack categories. Month 8 involved the design and implementation of the novel Asymmetric SMOTE-ENN pipeline, addressing the class imbalance problem through class-capped oversampling and Edited Nearest Neighbours boundary cleaning. Month 9 focused on the Champion Model Selection Framework, training both a Distance-Weighted KNN and a Balanced Random Forest, with Gini Impurity-based Feature Selection reducing the feature space by 74.4% to the top 20 attributes. Months 10 and 11 were dedicated to system engineering, integrating the trained model into a real-time Django Channels WebSocket inference pipeline with sub-5 ms detection latency, and building a live React.js dashboard for traffic monitoring and incident management. The final month was reserved for rigorous end-to-end system testing using live attack scenarios (Nmap Port Scanning, Hydra SSH Brute-force, and volumetric DoS tools), performance benchmarking, and the preparation of this blackbook report.
