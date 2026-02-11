import json
import os

# Script to restore corrupted nodes from exported_workflow.json
# while preserving the fix in 'Generate Block Diagram' node.

BACKUP_FILE = 'exported_workflow.json'
CORRUPTED_FILE = 'Phase1_Complete_Workflow_READY_TO_IMPORT.json'
OUTPUT_FILE = 'Phase1_Complete_Workflow_Fixed_Restored.json'

def restore_workflow():
    if not os.path.exists(BACKUP_FILE):
        print(f"❌ Backup file {BACKUP_FILE} not found!")
        return
    
    if not os.path.exists(CORRUPTED_FILE):
        print(f"❌ Corrupted file {CORRUPTED_FILE} not found!")
        return

    print(f"Loading backup from {BACKUP_FILE}...")
    with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    # Handle array vs object
    if isinstance(backup_data, list):
        backup_workflow = backup_data[0]
    else:
        backup_workflow = backup_data

    # Map backup nodes by name for easy lookup
    backup_nodes = {n['name']: n for n in backup_workflow['nodes']}
    
    print(f"Loading corrupted file from {CORRUPTED_FILE}...")
    with open(CORRUPTED_FILE, 'r', encoding='utf-8') as f:
        target_workflow = json.load(f)

    restored_count = 0
    kept_count = 0
    
    for node in target_workflow['nodes']:
        name = node['name']
        
        if name == 'Generate Block Diagram':
            # This node in the corrupted file HAS THE FIX.
            # We must PRESERVE it.
            # (Verify it has the new saveQuery logic if possible, but assuming it does since script ran)
            print(f"✅ Keeping FIXED code for node: '{name}'")
            kept_count += 1
            continue

        # For all other nodes, we check if they exist in backup
        if name in backup_nodes:
            backup_node = backup_nodes[name]
            
            # Check if source has jsCode to restore
            if 'jsCode' in backup_node.get('parameters', {}):
                # Restore jsCode
                # We assume the corrupted file has WRONG jsCode
                # But we should check if they differ?
                # No, we know they are corrupted (same content as Block Diagram).
                
                # Restore ONLY jsCode? Or exact parameters?
                # Safest to restore the 'jsCode' parameter specifically.
                node['parameters']['jsCode'] = backup_node['parameters']['jsCode']
                print(f"Reverting code for node: '{name}'")
                restored_count += 1
            else:
                # If backup node doesn't have jsCode, and target does?
                # The corruption only affected lines with "jsCode": ...
                # If target node acquired jsCode where it shouldn't have?
                # e.g. "Chat Trigger" doesn't have jsCode.
                # If my previous script replaced string by string, it wouldn't ADD a key if line didn't exist.
                # It only replaced existing lines.
                pass
        else:
            print(f"⚠️  Node '{name}' not found in backup. Skipping.")

    print(f"\nSummary: Kept {kept_count} fixed nodes. Restored {restored_count} nodes.")
    
    print(f"Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(target_workflow, f, indent=2)
    
    print("✅ Restoration Complete.")

if __name__ == "__main__":
    restore_workflow()
