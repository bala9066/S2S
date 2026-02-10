// ==========================================
// GENERATE VISUAL BLOCK DIAGRAM
// Add this node AFTER "Generate Block Diagram"
// and BEFORE "Show Diagram & Wait Approval"
// ==========================================

const diagram = $json.block_diagram;
const projectName = $json.project_name || 'Hardware_Project';
const systemType = $json.system_type || 'Digital_Controller';

// Function to convert block diagram to Mermaid syntax
function blockDiagramToMermaid(diagramJson) {
  let mermaid = "flowchart TD\n";

  // Add blocks with styling based on type
  const blocks = diagramJson.blocks || [];
  blocks.forEach(block => {
    const id = block.id;
    const label = block.label.replace(/"/g, "'");
    const type = block.type || 'default';

    // Choose shape based on type
    if (type === 'processor') {
      mermaid += `    ${id}[["${label}"]]\n`;  // Double bracket for processor
    } else if (type.includes('power')) {
      mermaid += `    ${id}("${label}")\n`;  // Rounded for power
    } else if (type === 'interface') {
      mermaid += `    ${id}["${label}"]\n`;  // Rectangle for interface
    } else {
      mermaid += `    ${id}["${label}"]\n`;  // Default rectangle
    }
  });

  mermaid += "\n";

  // Add connections
  const connections = diagramJson.connections || [];
  connections.forEach(conn => {
    if (conn.from && conn.to) {
      const label = conn.label || '';
      if (label) {
        mermaid += `    ${conn.from} -->|"${label.replace(/"/g, "'")}\"| ${conn.to}\n`;
      } else {
        mermaid += `    ${conn.from} --> ${conn.to}\n`;
      }
    }
  });

  mermaid += "\n";

  // Add styling
  mermaid += `
    classDef processorStyle fill:#4A90E2,stroke:#2E5C8A,stroke-width:3px,color:#fff
    classDef powerStyle fill:#F5A623,stroke:#D68910,stroke-width:2px,color:#fff
    classDef interfaceStyle fill:#7ED321,stroke:#5FA319,stroke-width:2px,color:#fff
  `;

  return mermaid;
}

// Function to encode Mermaid to base64 for image URL
function mermaidToImageURL(mermaidCode) {
  const encoded = Buffer.from(mermaidCode).toString('base64');
  return `https://mermaid.ink/img/${encoded}`;
}

// Generate Mermaid code
const mermaidCode = blockDiagramToMermaid(diagram);

// Generate image URL (can be embedded in HTML or displayed)
const imageURL = mermaidToImageURL(mermaidCode);

// Generate HTML preview
const htmlPreview = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Block Diagram - ${projectName}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
        }
        .info {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .diagram {
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
            overflow-x: auto;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .buttons {
            margin: 30px 0;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        button {
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .approve {
            background: #28a745;
            color: white;
        }
        .approve:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .reject {
            background: #dc3545;
            color: white;
        }
        .reject:hover {
            background: #c82333;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .modify {
            background: #ffc107;
            color: #333;
        }
        .modify:hover {
            background: #e0a800;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        #response {
            margin-top: 20px;
            padding: 20px;
            border-radius: 5px;
            display: none;
            font-size: 16px;
        }
        .copy-btn {
            background: #007bff;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-top: 10px;
        }
        .copy-btn:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Block Diagram Preview</h1>

        <div class="info">
            <strong>Project:</strong> ${projectName}<br>
            <strong>System Type:</strong> ${systemType}<br>
            <strong>Generated:</strong> ${new Date().toISOString()}
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">${diagram.blocks.length}</div>
                <div class="stat-label">Total Blocks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${diagram.connections.length}</div>
                <div class="stat-label">Connections</div>
            </div>
        </div>

        <div class="diagram">
            <div class="mermaid">
${mermaidCode}
            </div>
        </div>

        <div class="buttons">
            <button class="approve" onclick="approve()">✅ APPROVE</button>
            <button class="reject" onclick="reject()">❌ REJECT</button>
            <button class="modify" onclick="modify()">✏️ MODIFY</button>
        </div>

        <div id="response"></div>
    </div>

    <script>
        mermaid.initialize({ startOnLoad: true, theme: 'default' });

        function copyToClipboard(text) {
            navigator.clipboard.writeText(text).then(() => {
                alert('Copied to clipboard! Paste this in n8n chat.');
            });
        }

        function approve() {
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.style.background = '#d4edda';
            responseDiv.style.color = '#155724';
            responseDiv.innerHTML = \`
                <strong>✅ APPROVED!</strong><br>
                <p>Copy this text and paste in n8n chat:</p>
                <code style="background: #fff; padding: 10px; display: block; border-radius: 4px; margin: 10px 0;">APPROVE</code>
                <button class="copy-btn" onclick="copyToClipboard('APPROVE')">📋 Copy</button>
            \`;
        }

        function reject() {
            const reason = prompt('Why are you rejecting? (optional)');
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.style.background = '#f8d7da';
            responseDiv.style.color = '#721c24';
            const text = 'REJECT' + (reason ? ': ' + reason : '');
            responseDiv.innerHTML = \`
                <strong>❌ REJECTED!</strong><br>
                <p>Copy this text and paste in n8n chat:</p>
                <code style="background: #fff; padding: 10px; display: block; border-radius: 4px; margin: 10px 0;">\${text}</code>
                <button class="copy-btn" onclick="copyToClipboard('\${text}')">📋 Copy</button>
            \`;
        }

        function modify() {
            const changes = prompt('What changes do you want?');
            const responseDiv = document.getElementById('response');
            responseDiv.style.display = 'block';
            responseDiv.style.background = '#fff3cd';
            responseDiv.style.color = '#856404';
            const text = 'MODIFY: ' + (changes || 'Please make changes');
            responseDiv.innerHTML = \`
                <strong>✏️ MODIFICATION REQUESTED!</strong><br>
                <p>Copy this text and paste in n8n chat:</p>
                <code style="background: #fff; padding: 10px; display: block; border-radius: 4px; margin: 10px 0;">\${text}</code>
                <button class="copy-btn" onclick="copyToClipboard('\${text}')">📋 Copy</button>
            \`;
        }
    </script>
</body>
</html>`;

// Save HTML to file (n8n can write to disk)
const fs = require('fs');
const outputPath = `/mnt/data/outputs/${projectName}_block_diagram.html`;
fs.writeFileSync(outputPath, htmlPreview);

console.log(`[VISUAL DIAGRAM] Generated at: ${outputPath}`);
console.log(`[VISUAL DIAGRAM] Image URL: ${imageURL}`);

return {
  json: {
    ...($json),
    mermaid_code: mermaidCode,
    diagram_image_url: imageURL,
    diagram_html_path: outputPath,
    diagram_html_url: `file://${outputPath}`,
    visual_preview_ready: true
  }
};
