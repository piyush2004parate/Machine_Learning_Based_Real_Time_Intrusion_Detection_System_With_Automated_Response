import pandas as pd

try:
    df = pd.read_csv('UNSW_Train_Test Datasets/UNSW_NB15_training-set.csv')
    
    dos = df[df['attack_cat'] == 'DoS']
    normal = df[df['label'] == 0]
    
    print("--- DOS ATTACK FLOW STATS (Training Data) ---")
    print(f"Avg spkts (Source Packets): {dos['spkts'].mean():.2f}")
    print(f"Avg rate (Packets/sec): {dos['rate'].mean():.2f}")
    print(f"Avg sbytes (Source Bytes): {dos['sbytes'].mean():.2f}")
    print(f"Avg sload (Source Bits/sec): {dos['sload'].mean():.2f}")
    
    print("\n--- SINGLE SYN PACKET METRICS (User Live Data) ---")
    print("spkts: 1")
    print("rate: 0")
    print("sbytes: 168")
    print("sload: 0")
    
    print("\nCONCLUSION:")
    if dos['rate'].mean() > 1000 and dos['spkts'].mean() > 10:
        print("The training dataset is based on aggregated network flows (many packets combined).")
        print("The live system is extracting features per individual packet (or short unfinished flows).")
        print("The KNN model classifies individual SYN packets (spkts=1, rate=0) as Normal because they don't match the heavy volumes of an aggregated DoS flow.")

except Exception as e:
    print("Error:", e)
