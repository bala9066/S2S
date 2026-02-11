import json

# Final Fix: Incremental saveQuery
js_template = r'''const parsed = $json.parsed_requirements || {};
const projectName = $json.project_name || 'Hardware_Project';
const systemType = $json.system_type || 'Digital_Controller';
const startId = Date.now().toString().slice(-4);
let bid = parseInt(startId);

// Create base diagram structure
const diagram = { 
  version:'1.0', 
  type:'hardware_block_diagram', 
  metadata:{project:projectName,system_type:systemType,overview:parsed.system_overview||''}, 
  blocks:[], 
  connections:[] 
};

// Use parsed blocks if available
if (parsed.block_diagram_components && parsed.block_diagram_components.length > 0) {
  diagram.blocks = parsed.block_diagram_components;
  if (parsed.signal_flow) diagram.connections = parsed.signal_flow;
} else {
  // Fallback: Generate basic blocks based on type
  const primary = parsed.primary_components || {};
  const proc = primary.processor || {type:'MCU'};
  
  diagram.blocks.push({id:"B" + bid, type:'processor',name:proc.specific_part||proc.type,specs:proc.manufacturer||''});
  const pid = "B" + bid; bid++;
  
  const power = primary.power || {};
  diagram.blocks.push({id:"B" + bid,type:'power_input',name:'Power Input',specs:power.input_voltage||'12V'});
  const pwid = "B" + bid; bid++;
  
  if (power.rails_needed) {
    (power.rails_needed||[]).forEach(r => {
      const v = typeof r==='object'?r.voltage:r;
      const specs = typeof r==='object' ? (r.current + " for " + r.purpose) : v;
      diagram.blocks.push({id:"B" + bid,type:'regulator',name:"DC-DC " + v, specs:specs});
      diagram.connections.push({from:pwid,to:"B" + bid,signal:'DC'});
      diagram.connections.push({from:"B" + bid,to:pid,signal:v});
      bid++;
    });
  }
}

// --- MERMAID GENERATION ---
const blocksStr = diagram.blocks.map(b => {
  const label = (b.name||b.type).replace(/["\\]/g, '');
  const details = (b.specs||b.type).replace(/["\\]/g, '');
  return '    ' + b.id + '["' + label + '<br/>' + details + '"]';
}).join('\n');

const connStr = diagram.connections.map(c => {
  const label = (c.signal||c.specs||'').replace(/["\\]/g, '');
  return '    ' + c.from + ' -->|' + label + '| ' + c.to;
}).join('\n');

const mermaidCode = "graph TD\n" + blocksStr + "\n\n" + connStr + "\n\nclassDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;";

// --- HTML GENERATION ---
const htmlContent = '<!DOCTYPE html><html><head><title>' + projectName + '</title><script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";mermaid.initialize({ startOnLoad: true });</scr' + 'ipt><style>body{font-family:sans-serif;padding:20px;}.mermaid{margin:20px 0;padding:20px;border:1px solid #ddd;border-radius:5px;}</style></head><body><h1>' + projectName + ' - Block Diagram</h1><div class="mermaid">' + mermaidCode + '</div><hr/><pre>' + mermaidCode + '</pre></body></html>';

// --- FILE SAVING ---
let savePath = '';
try {
  const fs = require('fs');
  const path = require('path');
  const outputDir = '/mnt/data/outputs';
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, {recursive:true});
  const filename = projectName.replace(/[^a-z0-9]/gi, '_') + '_diagram.html';
  savePath = path.join(outputDir, filename);
  fs.writeFileSync(savePath, htmlContent);
} catch(e) { 
  savePath = 'Error saving: ' + e.message; 
}

// --- ASCII GENERATION ---
const asciiTitle = "\n+==============================================================================+\n|  HARDWARE BLOCK DIAGRAM                                                       |\n+==============================================================================+\n|  Project: " + projectName.substring(0,30).padEnd(30) + "                           |\n|  Type: " + systemType.padEnd(35) + "                           |\n+==============================================================================+\n\n";

const asciiOverview = "SYSTEM OVERVIEW:\n" + (parsed.system_overview || systemType + ' System') + "\n\n";

const asciiBlocks = "BLOCK DIAGRAM COMPONENTS:\n" + diagram.blocks.map((b,i) => {
  return "  [" + (b.id||i+1) + "] " + (b.name||'Component').padEnd(25) + " | " + (b.type).padEnd(15) + " | " + (b.specs||'');
}).join('\n') + "\n\n";

const asciiSignals = "SIGNAL FLOW:\n" + diagram.connections.slice(0,13).map((c,i) => {
  return "  " + c.from + " --> " + c.to + " (" + (c.signal||c.specs||'data') + ")";
}).join('\n') + "\n\n";

const asciiMermaid = "MERMAID CODE (Copy to Mermaid Live Editor):\n\n" + mermaidCode + "\n\n";

const asciiFooter = "HTML Preview saved to: " + savePath;

const asciiDiagram = asciiTitle + asciiOverview + asciiBlocks + asciiSignals + asciiMermaid + asciiFooter;


function esc(s) { return s == null ? '' : String(s).split("'").join("''"); }

let q = 'INSERT INTO pending_approvals (session_id, project_name, system_type, block_diagram, parsed_requirements, ascii_diagram, original_requirements) VALUES (';
q += "'" + esc($json.session_id) + "',";
q += "'" + esc(projectName) + "',";
q += "'" + esc(systemType) + "',";
q += "'" + esc(JSON.stringify(diagram)) + "',";
q += "'" + esc(JSON.stringify(parsed)) + "',";
q += "'" + esc(asciiDiagram) + "',";
q += "'" + esc($json.original_requirements||'') + "')";
q += ' ON CONFLICT (session_id) DO UPDATE SET block_diagram=EXCLUDED.block_diagram, parsed_requirements=EXCLUDED.parsed_requirements, ascii_diagram=EXCLUDED.ascii_diagram, created_at=NOW()';

const saveQuery = q;

return { json: { ...($json), block_diagram:diagram, ascii_diagram:asciiDiagram, save_query:saveQuery, mermaid_code:mermaidCode, html_path:savePath } };'''

# Perform replacements
js_code = js_template 

safe_json_value = json.dumps(js_code)
replacement_line = f'        "jsCode": {safe_json_value}'

target_file = 'Phase1_Complete_Workflow_READY_TO_IMPORT.json'
new_lines = []
found = False

with open(target_file, 'r', encoding='utf-8') as f:
    for line in f:
        # Match "jsCode":   (generic match)
        if '"jsCode":' in line:
            new_lines.append(replacement_line + '\n')
            found = True
        else:
            new_lines.append(line)

if found:
    with open(target_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("✅ Fixed workflow file (Incremental SaveQuery).")
else:
    print("❌ Could not find target line to replace.")
