import os

filepath = r'c:\Users\sanja\OneDrive\Desktop\Machine_Learning_Based_RealTime_Intrusion_Detection_System-main\Backend\ml_ids_project\api\consumers.py'

with open(filepath, 'r') as f:
    text = f.read()

# Update sleep from 1 to 0.1
text = text.replace('await asyncio.sleep(1)', 'await asyncio.sleep(0.1)')

# Find where KNN evaluation starts:
# We only want to run KNN and enqueue if it meets rate limits.
# But wait, we can just wrap the `if anomaly_detector is not None:` and `data = ...` down to `out_queue.put` in an `if` block.

lines = text.split('\n')
new_lines = []

for line in lines:
    if 'flow_features = {' in line:
        # Before flow features, insert the rate limiter check
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(indent + 'now_ts = features["timestamp"]')
        new_lines.append(indent + 'last_emit = st.get("last_emit_ts", 0)')
        new_lines.append(indent + 'if total_pkts == 1 or total_pkts % 50 == 0 or (now_ts - last_emit) > 1.0:')
        new_lines.append(indent + '    st["last_emit_ts"] = now_ts')
        new_lines.append(indent + '    ' + line.lstrip())
    elif 'if anomaly_detector is not None:' in line:
        pass # we will manually indent
new_lines = []

inside_rate_limit = False
indent_amount = "                "

for line in lines:
    if line.startswith(indent_amount + 'flow_features = {'):
        new_lines.append(indent_amount + 'last_emit = st.get("last_emit_ts", 0)')
        new_lines.append(indent_amount + 'if total_pkts == 1 or total_pkts % 100 == 0 or (now_ts - last_emit) > 1.0:')
        new_lines.append(indent_amount + '    st["last_emit_ts"] = now_ts')
        new_lines.append(indent_amount + '    ' + line.lstrip())
        inside_rate_limit = True
        continue
        
    if inside_rate_limit:
        if line.startswith(indent_amount) and line.lstrip() != "":
            # Indent another 4 spaces
            new_lines.append("    " + line)
        elif line == "":
            new_lines.append(line)
        else:
            # We exited the block that has `indent_amount`
            if not line.startswith(indent_amount):
                inside_rate_limit = False
                new_lines.append(line)
            else:
                new_lines.append("    " + line)
    else:
        new_lines.append(line)

with open(r'c:\Users\sanja\OneDrive\Desktop\Machine_Learning_Based_RealTime_Intrusion_Detection_System-main\Backend\ml_ids_project\api\consumers_patched.py', 'w') as f:
    f.write('\n'.join(new_lines))
print("Done")
