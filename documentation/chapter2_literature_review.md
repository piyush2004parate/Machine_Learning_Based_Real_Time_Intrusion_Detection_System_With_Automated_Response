# CHAPTER 2: LITERATURE REVIEW

---

## 2.1 Overview of Security Architectures

The architectural evolution of Network Intrusion Detection Systems (NIDS) has transitioned through three distinct generations. The first generation, dominated by rule-based detection, operates on the principle of pattern matching against a localized database of known malicious strings. While highly effective in identifying historical attack vectors with zero false positives, these systems are functionally paralyzed when encountering zero-day vulnerabilities or polymorphic threats that deviate even slightly from established signatures.

The second generation introduced anomaly-based detection, utilizing statistical profiles of normal network behavior. Any deviation from this baseline is flagged as a potential threat. While this approach allows for the detection of novel attacks, it is notoriously prone to high false-positive rates in dynamic enterprise environments where legitimate network growth can be misclassified as anomalous activity.

The third generation, which characterizes the present research, incorporates Machine Learning and Ensemble Learning. Unlike simple statistical thresholding, these systems can learn non-linear relationships within high-dimensional network flow data, demonstrating significantly higher detection rates and lower response latencies compared to traditional rule-based logic.

---

## 2.2 Detailed Literature Survey

This section provides a structured summary of foundational research papers, focusing on their methodologies, core contributions, and identified constraints.

| Ref | Author / Year | Technique / Approach | Key Contribution | Limitations |
| :--- | :--- | :--- | :--- | :--- |
| [1] | Sharafaldin et al. (2019) | Dataset Framework | Development of the enterprise-grade CSE-CIC-IDS2018 benchmark. | Extreme class imbalance; no mitigation implementation. |
| [3] | Khraisat et al. (2019) | Hybrid IDS Survey | Comprehensive taxonomy of intrusion detection methods. | Lack of practical real-time execution metrics. |
| [4] | Vinayakumar et al. (2019)| Deep Learning (CNN/RNN) | Benchmarking high-fidelity feature learning in IDS. | High computational overhead and inference latency. |
| [5] | Mahfouz et al. (2017) | Supervised Learning | Systematic comparison of KNN on large-scale datasets. | Distance-based models struggle with high-dimensional noise. |
| [7] | Chawla et al. (2002) | SMOTE Engineering | Established the baseline for minority class oversampling. | Prone to over-generalization without boundary cleaning. |
| [8] | Batista et al. (2004) | Hybrid Sampling | Integrated SMOTE with ENN for boundary editing. | Did not specify IDS-specific False Positive Trap issues. |
| [9] | Garcia-Teodoro et al. (2009)| Anomaly Detection | Defined the taxonomy of anomaly behavior behaviors. | High false alarms due to transient network dynamics. |

---

## 2.3 Machine Learning Classifiers in Network Security

A significant body of research focuses on selecting the optimal classifier for high-throughput traffic.

### 2.3.1 Proximity-based Models
K-Nearest Neighbors (KNN) has been widely used due to its simplicity and effectiveness in lower-dimensional spaces. However, distance-based methods suffer from exponential increases in inference time as the dataset grows—a phenomenon known as the curse of dimensionality. Furthermore, these models are highly sensitive to the scaling of features and the noise introduced during synthetic data balancing, often leading to a degradation in accuracy when applied to modern, heterogeneous enterprise traffic.

### 2.3.2 Ensemble Learning Models
Ensemble techniques, specifically Random Forest and XGBoost, have emerged as superior alternatives for tabular network data. Unlike single-estimator models, an ensemble utilizing uncorrelated decision trees can significantly reduce the risk of overfitting. By aggregating the majority consensus of multiple trees, the system provides high robustness against the outliers inherently present in bursty network traffic, such as the traffic spikes seen during a Distributed Denial of Service (DDoS) event.

---

## 2.4 Data Engineering and the Class Imbalance Problem

The primary challenge in network security research is the extreme class imbalance present in modern benchmarks.

### 2.4.1 Synthetic Minority Oversampling (SMOTE)
To address the scarcity of minority attack samples—such as Web Attacks or SQL Injection—researchers frequently employ the Synthetic Minority Oversampling Technique. This method works by interpolating new samples along the line segments joining the nearest minority neighbors. However, a critical drawback exists: in extreme cases where a class has very few real observations, unrestricted oversampling generates a massive volume of artificial instances. This distorts the feature space, causing the model to learn noise as malicious, leading to a significant drop in benign-class recall during real-world deployment.

### 2.4.2 Hybrid Resampling and Boundary Cleaning
Recent developments suggest that the combination of oversampling with undersampling provides cleaner decision boundaries. Using a hybrid approach, such as combining SMOTE with Edited Nearest Neighbours (ENN), allows for the removal of ambiguous samples that fall within class overlap regions. By "pruning" the synthetic noise, the system can maintain the statistical integrity of the original traffic distribution while ensuring minority visibility.

---

## 2.5 Comparative Analysis Table

Summary of different approaches compared to the proposed system architecture.

| Methodology | Balancing Strategy | Model Used | Strengths | Major Weakness |
| :--- | :--- | :--- | :--- | :--- |
| Standard IDS | None | Signature-matching | Zero False Positives | Cannot detect novel threats |
| Laboratory ML | Uniform SMOTE | Decision Trees | High Accuracy | Fails on real network noise |
| Distance-based | Oversampling | KNN | Easy to implement | High latency; FP Trap |
| **Proposed Work** | **Asymmetric SMOTE-ENN** | **Ensemble Learning** | **Deep Isolation** | **None identified** |

---

## 2.6 Research Gaps and Limitations

The following research gaps were identified in existing literature:

1.  **Response Latency:** Most research focuses on offline accuracy rather than online latency. There is a lack of systems providing end-to-end classification and mitigation in under 10 milliseconds.
2.  **Synthetic Distortion:** Many papers achieve high accuracy by training on artificially balanced data but fail when deployed on real network traffic, which is predominantly benign.
3.  **Unidirectional Mitigation:** Existing automated responses often only block inbound traffic. This allows the host machine to continue leaking defensive responses, alerting the attacker to the system's presence.
4.  **Explainability:** There is a lack of stateful behavioral integration that clearly differentiates between reconnaissance, credential attacks, and volumetric floods for administrative review.
