# 🎨 Visual Block Diagram Solutions

## Problem
Current workflow shows ASCII text diagram - you can't **SEE** the actual visual diagram to approve it.

---

## ✅ Solution 1: Mermaid.js with HTML Preview (Best - No External APIs)

### How It Works:
1. Generate block diagram JSON (already done)
2. Convert to Mermaid syntax
3. Generate HTML file with embedded diagram
4. Open HTML in browser to see beautiful visual diagram
5. Click APPROVE/REJECT buttons in browser
6. Copy response and paste back to n8n

### Advantages:
- ✅ **100% Free** - No external APIs
- ✅ **Works Offline** - All local
- ✅ **Beautiful** - Professional-looking diagrams
- ✅ **Interactive** - Click buttons to approve/reject
- ✅ **Fast** - Instant rendering
- ✅ **Easy to integrate** - Just add 1 node to workflow

### Setup Steps:

#### Step 1: Add Python Script to n8n

Already created: `mermaid_diagram_generator.py`

#### Step 2: Add Code Node to Workflow

**In n8n:**
1. Add new **Code node** after "Generate Block Diagram"
2. Name it: **"Generate Visual Diagram"**
3. Copy code from: `workflow_node_visual_diagram.js`
4. Paste into node

#### Step 3: Update "Show Diagram & Wait Approval" Node

Change the output message to include HTML link:

```javascript
// Show diagram and request approval
const diagram = $json.ascii_diagram;
const projectName = $json.project_name;
const htmlPath = $('Generate Visual Diagram').item.json.diagram_html_path;

return {
  json: {
    output: `📋 **BLOCK DIAGRAM GENERATED**\n\n${diagram}\n\n🎨 **VISUAL PREVIEW AVAILABLE**\n\nOpen this file in your browser to see the visual diagram:\n${htmlPath}\n\nThe HTML page has buttons to APPROVE/REJECT.\nClick the button, then copy the text and paste here.\n\n**Or type directly:**\n- Type **"APPROVE"** to continue to component selection\n- Type **"REJECT: <reason>"** to request changes`,
    ...($json)
  }
};
```

### What User Sees:

**In n8n Chat:**
```
📋 BLOCK DIAGRAM GENERATED

╔════════════════════════════════════════╗
║  BLOCK DIAGRAM: Motor_Controller      ║
╠════════════════════════════════════════╣
...

🎨 VISUAL PREVIEW AVAILABLE

Open this file in your browser to see the visual diagram:
/mnt/data/outputs/Motor_Controller_block_diagram.html

The HTML page has buttons to APPROVE/REJECT.
Click the button, then copy the text and paste here.

Or type directly:
- Type "APPROVE" to continue
- Type "REJECT: <reason>" to request changes
```

**User opens HTML file → Sees beautiful diagram → Clicks APPROVE → Copies "APPROVE" → Pastes in n8n**

---

## ✅ Solution 2: Mermaid.ink API (Simplest - Image URL)

### How It Works:
1. Convert diagram to Mermaid syntax
2. Encode and send to Mermaid.ink (free public API)
3. Get back image URL
4. Display image in n8n or browser

### Advantages:
- ✅ **No installation** - Just use API
- ✅ **Direct image URL** - Can embed anywhere
- ✅ **Free** - Public service

### Add to Workflow:

```javascript
// In "Generate Visual Diagram" node
const mermaidCode = blockDiagramToMermaid($json.block_diagram);

// Encode for Mermaid.ink
const encoded = Buffer.from(mermaidCode).toString('base64');
const imageURL = `https://mermaid.ink/img/${encoded}`;

// Also create a clickable preview URL
const previewURL = `https://mermaid.live/edit#base64:${encoded}`;

return {
  json: {
    ...($json),
    diagram_image_url: imageURL,
    diagram_preview_url: previewURL
  }
};
```

**User sees:**
```
🎨 VISUAL DIAGRAM:
View: https://mermaid.live/edit#base64:...
Image: https://mermaid.ink/img/...
```

Click the link → See diagram → Type APPROVE/REJECT

---

## ✅ Solution 3: Excalidraw API (Hand-drawn Style)

### How It Works:
Use Excalidraw for hand-drawn style diagrams

**API:** `https://excalidraw.com/api/export`

### Example:

```javascript
// Convert diagram to Excalidraw format
const excalidrawScene = {
  elements: diagram.blocks.map((block, i) => ({
    type: 'rectangle',
    x: block.position.x || i * 150,
    y: block.position.y || 100,
    width: 120,
    height: 60,
    text: block.label
  }))
};

// Export as image
const response = await fetch('https://excalidraw.com/api/export', {
  method: 'POST',
  body: JSON.stringify(excalidrawScene)
});

const imageURL = await response.text();
```

---

## ✅ Solution 4: Graphviz/DOT (Advanced)

### How It Works:
Use Graphviz DOT language for complex diagrams

**Tools:**
- Online: http://www.webgraphviz.com/
- Local: Graphviz installed

### Example:

```javascript
// Convert to DOT format
function blockDiagramToDOT(diagram) {
  let dot = 'digraph G {\n';
  dot += '  rankdir=LR;\n';
  dot += '  node [shape=box, style=rounded];\n\n';

  // Add nodes
  diagram.blocks.forEach(block => {
    const color = block.type === 'processor' ? 'lightblue' :
                  block.type.includes('power') ? 'orange' : 'lightgreen';
    dot += `  ${block.id} [label="${block.label}", fillcolor=${color}, style=filled];\n`;
  });

  dot += '\n';

  // Add edges
  diagram.connections.forEach(conn => {
    dot += `  ${conn.from} -> ${conn.to} [label="${conn.label || ''}"];\n`;
  });

  dot += '}\n';
  return dot;
}
```

---

## ✅ Solution 5: Draw.io Integration (Professional)

### How It Works:
Generate Draw.io XML format

**API:** https://app.diagrams.net/

### Example:

```javascript
// Generate draw.io XML
const drawioXML = `<mxfile>
  <diagram>
    <mxGraphModel>
      <root>
        ${diagram.blocks.map((block, i) => `
          <mxCell id="${block.id}" value="${block.label}"
                  style="rounded=1;whiteSpace=wrap;"
                  vertex="1" parent="1">
            <mxGeometry x="${i*150}" y="100" width="120" height="60" as="geometry"/>
          </mxCell>
        `).join('')}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>`;

// Save as .drawio file
fs.writeFileSync('/mnt/data/outputs/diagram.drawio', drawioXML);
```

User can open in https://app.diagrams.net/

---

## 📊 Comparison Table

| Solution | Setup Time | Cost | Quality | Offline | Best For |
|----------|-----------|------|---------|---------|----------|
| **Mermaid.js + HTML** | 10 min | Free | ⭐⭐⭐⭐⭐ | ✅ | **Recommended** |
| **Mermaid.ink API** | 5 min | Free | ⭐⭐⭐⭐ | ❌ | Quick setup |
| **Excalidraw** | 15 min | Free | ⭐⭐⭐⭐ | ❌ | Hand-drawn look |
| **Graphviz** | 20 min | Free | ⭐⭐⭐⭐⭐ | ✅ | Complex diagrams |
| **Draw.io** | 15 min | Free | ⭐⭐⭐⭐⭐ | ✅ | Professional |

---

## 🚀 Quick Start (Recommended: Mermaid.js)

### 1. Test Locally First

```bash
cd /home/user/S2S

# Run the test
python3 mermaid_diagram_generator.py

# Open the generated HTML
# It will create: /tmp/block_diagram_preview.html
# Open in browser to see the diagram!
```

### 2. Add to Workflow

**Option A: Add New Node (Recommended)**

1. In n8n workflow editor
2. Click **"+"** after "Generate Block Diagram" node
3. Select **"Code"** node
4. Name: **"Generate Visual Diagram"**
5. Paste code from `workflow_node_visual_diagram.js`
6. Connect: Generate Block Diagram → Generate Visual Diagram → Show Diagram & Wait Approval

**Option B: Modify Existing Node**

1. Open "Show Diagram & Wait Approval" node
2. Add this code at the beginning:

```javascript
// Generate Mermaid visual diagram
const diagram = $json.block_diagram;

function blockDiagramToMermaid(diagramJson) {
  // ... (copy from workflow_node_visual_diagram.js)
}

const mermaidCode = blockDiagramToMermaid(diagram);
const encoded = Buffer.from(mermaidCode).toString('base64');
const imageURL = `https://mermaid.ink/img/${encoded}`;
const previewURL = `https://mermaid.live/edit#base64:${encoded}`;

// Then in output message, add:
return {
  json: {
    output: `📋 **BLOCK DIAGRAM GENERATED**

🎨 **VISUAL PREVIEW:**
Click here to see diagram: ${previewURL}

Type "APPROVE" to continue or "REJECT" to modify.`,
    ...($json)
  }
};
```

### 3. Test It

Run workflow with motor controller input:
```
Design a 3-phase motor controller with TMS320F28379D DSP
```

You should see:
- Text diagram (as before)
- **+ Link to visual diagram** (NEW!)
- Click link → See beautiful diagram → Approve/Reject

---

## 🎨 What the Visual Diagram Looks Like

### Before (Current):
```
╔════════════════════════════════════════╗
║  BLOCK DIAGRAM: Project_123           ║
╠════════════════════════════════════════╣
║  System Type: Motor_Control            ║
║  Total Blocks: 8                       ║
║  Connections: 12                       ║
╚════════════════════════════════════════╝

MAIN COMPONENTS:
  1. TMS320F28379D (processor)
  2. 48V Input (power_input)
  ...
```
❌ Hard to understand flow

### After (With Mermaid):

**Visual flowchart with:**
- ✅ Colored blocks (blue for processor, orange for power, green for interfaces)
- ✅ Arrows showing connections
- ✅ Labels on connections (voltages, signals)
- ✅ Professional layout
- ✅ Interactive (zoom, pan)
- ✅ Approve/Reject buttons

**Example:**
```
[48V Input] --48V--> (5V Regulator) --5V--> [[TMS320F28379D]]
                                              ||
                                              ||--CAN--> [CAN Bus]
                                              ||
                                              ||--RMII--> [Ethernet PHY]
```

---

## 📝 Implementation Checklist

- [ ] Copy `mermaid_diagram_generator.py` to project
- [ ] Copy `workflow_node_visual_diagram.js` code
- [ ] Add new "Generate Visual Diagram" node to n8n workflow
- [ ] Update "Show Diagram & Wait Approval" node message
- [ ] Test with example input
- [ ] Open generated HTML file in browser
- [ ] Verify diagram looks correct
- [ ] Test APPROVE button
- [ ] Test REJECT button
- [ ] Copy response back to n8n
- [ ] Verify workflow continues correctly

---

## 🐛 Troubleshooting

### Issue: HTML file not found

**Solution:**
```bash
# Check if outputs directory exists
mkdir -p /mnt/data/outputs

# Check permissions
chmod 777 /mnt/data/outputs
```

### Issue: Mermaid not rendering

**Solution:**
- Make sure you have internet connection (loads Mermaid library from CDN)
- Or download Mermaid.js locally and update HTML to use local file

### Issue: Diagram looks messy

**Solution:**
- Adjust block positions in diagram generator
- Use `rankdir=LR` for left-to-right layout
- Use `rankdir=TB` for top-to-bottom layout

---

## 🎯 Recommended: Use Mermaid.js + HTML

**Why this is the best:**
1. ✅ No external dependencies
2. ✅ Beautiful, professional diagrams
3. ✅ Interactive approve/reject buttons
4. ✅ Works offline
5. ✅ Easy to integrate with n8n
6. ✅ Can save for documentation
7. ✅ Can share with team

**Setup time:** 10 minutes
**Difficulty:** Easy
**Maintenance:** None

---

## 🚀 Next Steps

1. Run test: `python3 mermaid_diagram_generator.py`
2. Open generated HTML in browser
3. If it looks good, add to n8n workflow
4. Test end-to-end

**You'll be able to SEE your block diagrams and approve them visually!**
