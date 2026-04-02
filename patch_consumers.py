import os

filepath = r'c:\Users\sanja\OneDrive\Desktop\Machine_Learning_Based_RealTime_Intrusion_Detection_System-main\Backend\ml_ids_project\api\consumers.py'

with open(filepath, 'r') as f:
    text = f.read()

# Define the block we want to move
target_block = """                # KNN anomaly detection
                status = "Normal"
                severity = "Low"
                probs = []
                pred_idx = 0
                pred_prob = 0.0
                attack_type_detected = None  # Store detected attack type
                
                if anomaly_detector is not None:
                    try:
                        # Get prediction from KNN model
                        result = anomaly_detector.predict(features)
                        pred_label = result.get('label', 'Normal')
                        status = pred_label
                        severity = "Critical" if pred_label == "Anomalous" else "Low"
                        pred_idx = result.get('prediction', 0)
                        pred_prob = result.get('confidence', 0.0)
                        probs = [
                            result.get('probabilities', {}).get('normal', 0.0),
                            result.get('probabilities', {}).get('anomalous', 0.0)
                        ]
                        
                        # Classify attack type if anomalous
                        if pred_label == "Anomalous":
                            attack_type_detected = _classify_attack_type(
                                rate, is_sm_ips_ports, proto, state, service, 
                                st["spkts"], st["dpkts"], st.get("sjit", 0), st.get("djit", 0)
                            )
                    except Exception as ex:
                        print("Exception in KNN predict:", ex)
                        # If classifier fails, fall back to Normal
                        status, severity, probs, pred_idx, pred_prob = "Normal", "Low", [], 0, 0.0"""

# Replace it with an initialization block
initialization_block = """                # Initialize prediction variables explicitly here
                status = "Normal"
                severity = "Low"
                probs = []
                pred_idx = 0
                pred_prob = 0.0
                attack_type_detected = None"""

# Notice I fixed the print debugging so that if it still fails we see why

# Because of exact matching issues, we isolate the lines dynamically:
lines = text.split('\n')
start_idx = -1
end_idx = -1

for i, line in enumerate(lines):
    if "# KNN anomaly detection" in line:
        start_idx = i
    if "status, severity, probs, pred_idx, pred_prob =" in line and start_idx != -1:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    # Save the original KNN block, with exact original indentation
    original_knn_block = lines[start_idx:end_idx+1]
    
    # Replace that top section with the basic variables init
    for i in range(start_idx, end_idx+1):
        lines[i] = ""
    lines[start_idx] = initialization_block
    
    # Now find where to insert them back: before deriving label_val
    insert_idx = -1
    for i, line in enumerate(lines):
        if "# Derive numeric label from model prediction" in line:
            insert_idx = i
            break
            
    if insert_idx != -1:
        new_insert = []
        indent = "                "
        new_insert.append(indent + "flow_features = {")
        new_insert.append(indent + "    'dur': dur, 'spkts': st['spkts'], 'dpkts': st['dpkts'],")
        new_insert.append(indent + "    'sbytes': st['sbytes'], 'dbytes': st['dbytes'], 'rate': rate,")
        new_insert.append(indent + "    'sload': sload, 'dload': dload, 'sinpkt': st.get('last_s_dt') or 0,")
        new_insert.append(indent + "    'dinpkt': st.get('last_d_dt') or 0, 'sjit': st.get('sjit') or 0, 'djit': st.get('djit') or 0,")
        new_insert.append(indent + "    'sttl': st.get('sttl') or 0, 'dttl': st.get('dttl') or 0, 'swin': st.get('swin') or 0,")
        new_insert.append(indent + "    'stcpb': st.get('stcpb') or 0, 'dtcpb': st.get('dtcpb') or 0, 'synack': synack or 0,")
        new_insert.append(indent + "    'tcprtt': tcprtt or 0, 'ackdat': st.get('ackdat') or 0, 'smean': smean,")
        new_insert.append(indent + "    'dmean': dmean, 'ct_srv_src': ct_srv_src, 'ct_state_ttl': ct_state_ttl,")
        new_insert.append(indent + "    'ct_dst_ltm': ct_dst_ltm, 'ct_src_dport_ltm': ct_src_dport_ltm,")
        new_insert.append(indent + "    'ct_dst_sport_ltm': ct_dst_sport_ltm, 'ct_dst_src_ltm': ct_dst_src_ltm,")
        new_insert.append(indent + "    'ct_src_ltm': ct_src_ltm, 'ct_srv_dst': ct_srv_dst, 'is_sm_ips_ports': is_sm_ips_ports,")
        new_insert.append(indent + "}")
        
        # Modify the original block
        modified_block = []
        for b_line in original_knn_block:
            if "anomaly_detector.predict(features)" in b_line:
                modified_block.append(b_line.replace("features", "flow_features"))
            elif "rate, is_sm_ips_ports, proto, state, service," in b_line:
                modified_block.append(b_line.replace("proto", "protocol_str"))
            elif "except Exception:" in b_line:
                modified_block.append(b_line.replace("except Exception:", "except Exception as e:\n" + indent + "                        print(f'Prediction error: {e}')"))
            else:
                modified_block.append(b_line)
                
        lines = lines[:insert_idx] + new_insert + modified_block + lines[insert_idx:]
        
        with open(filepath, 'w') as f:
            f.write('\\n'.join(lines))
            
        print("Patch successfully applied! KNN evaluation moved to bottom.")
    else:
        print("Error: Could not find insert_idx")
else:
    print("Error: Could not find start/end bounds for knn block")
