import json

# Define JS code with placeholders to avoid escape hell
# Using raw string for the bulk of logic
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
  const proc = parsed.primary_components?.processor || {type:'MCU'};
  diagram.blocks.push({id:`B${bid}`,type:'processor',name:proc.specific_part||proc.type,specs:proc.manufacturer||''});
  const pid = `B${bid}`; bid++;
  
  const power = parsed.primary_components?.power || {};
  diagram.blocks.push({id:`B${bid}`,type:'power_input',name:'Power Input',specs:power.input_voltage||'12V'});
  const pwid = `B${bid}`; bid++;
  
  if (power.rails_needed) {
    (power.rails_needed||[]).forEach(r => {
      const v = typeof r==='object'?r.voltage:r;
      diagram.blocks.push({id:`B${bid}`,type:'regulator',name:`DC-DC ${v}`,specs:typeof r==='object'?`${r.current} for ${r.purpose}`:v});
      diagram.connections.push({from:pwid,to:`B${bid}`,signal:'DC'});
      diagram.connections.push({from:`B${bid}`,to:pid,signal:v});
      bid++;
    });
  }
}

// --- MERMAID GENERATION ---
const mermaidCode = `graph TD\n${diagram.blocks.map(b => {
  const label = (b.name||b.type).replace(/["\\]/g, '');
  const details = (b.specs||b.type).replace(/["\\]/g, '');
  return `    ${b.id}["${label}<br/>${details}"]`;
}).join('\n')}\n\n${diagram.connections.map(c => {
  const label = (c.signal||c.specs||'').replace(/["\\]/g, '');
  return `    ${c.from} -->|${label}| ${c.to}`;
}).join('\n')}\n\nclassDef default fill:#f9f9f9,stroke:#333,stroke-width:2px;`;

// --- HTML GENERATION ---
// Split script tag to avoid confusing parsers
const htmlContent = `<!DOCTYPE html><html><head><title>${projectName}</title><script type="module">import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';mermaid.initialize({ startOnLoad: true });</scr`+`ipt><style>body{font-family:sans-serif;padding:20px;}.mermaid{margin:20px 0;padding:20px;border:1px solid #ddd;border-radius:5px;}</style></head><body><h1>${projectName} - Block Diagram</h1><div class="mermaid">${mermaidCode}</div><hr/><pre>${mermaidCode}</pre></body></html>`;

// --- FILE SAVING ---
let savePath = '';
try {
  const fs = require('fs');
  const path = require('path');
  const outputDir = '/mnt/data/outputs';
  if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir, {recursive:true});
  const filename = `${projectName.replace(/[^a-z0-9]/gi, '_')}_diagram.html`;
  savePath = path.join(outputDir, filename);
  fs.writeFileSync(savePath, htmlContent);
} catch(e) { 
  savePath = 'Error saving: ' + e.message; 
}

// --- ASCII GENERATION ---
const asciiDiagram = `\n+==============================================================================+\n|  HARDWARE BLOCK DIAGRAM                                                       |\n+==============================================================================+\n|  Project: ${projectName.substring(0,30).padEnd(30)}                           |\n|  Type: ${systemType.padEnd(35)}                           |\n+==============================================================================+\n\nSYSTEM OVERVIEW:\n${parsed.system_overview || systemType + ' System'}\n\nBLOCK DIAGRAM COMPONENTS:\n${diagram.blocks.map((b,i) => `  [${b.id||i+1}] ${(b.name||'Component').padEnd(25)} | ${b.type.padEnd(15)} | ${b.specs||''}`).join('\n')}\n\nSIGNAL FLOW:\n${diagram.connections.slice(0,13).map((c,i) => `  ${c.from} --> ${c.to} (${c.signal||c.specs||'data'})`).join('\n')}\n\nMERMAID CODE (Copy to Mermaid Live Editor):\n___TRIPLE_BACKTICK___mermaid\n${mermaidCode}\n___TRIPLE_BACKTICK___\n\nHTML Preview saved to: ${savePath}`; 

function esc(s) { return s == null ? '' : String(s).split("'").join("''"); }
const saveQuery = 'INSERT INTO pending_approvals (session_id, project_name, system_type, block_diagram, parsed_requirements, ascii_diagram, original_requirements) VALUES (' + "'" + esc($json.session_id) + "','" + esc(projectName) + "','" + esc(systemType) + "','" + esc(JSON.stringify(diagram)) + "','" + esc(JSON.stringify(parsed)) + "','" + esc(asciiDiagram) + "','" + esc($json.original_requirements||'') + "')' + ' ON CONFLICT (session_id) DO UPDATE SET block_diagram=EXCLUDED.block_diagram, parsed_requirements=EXCLUDED.parsed_requirements, ascii_diagram=EXCLUDED.ascii_diagram, created_at=NOW()';

return { json: { ...($json), block_diagram:diagram, ascii_diagram:asciiDiagram, save_query:saveQuery, mermaid_code:mermaidCode, html_path:savePath } };'''

# Perform replacements
# Replace placeholder with explicitly escaped backticks
# r"\`" produces literal \` (backslash backtick) inside the JS code string
js_code = js_template.replace("___TRIPLE_BACKTICK___", r"\`\`\`")

# Generate just the value part to be used in "jsCode": VALUE
print(json.dumps(js_code))
