#!/usr/bin/env python3
"""
Block Diagram to Mermaid Converter
Converts JSON block diagram to Mermaid syntax for visual rendering
"""

def block_diagram_to_mermaid(diagram_json):
    """
    Convert block diagram JSON to Mermaid flowchart syntax

    Args:
        diagram_json: {
            "blocks": [
                {"id": "B1", "type": "processor", "label": "STM32F4"},
                {"id": "B2", "type": "power_input", "label": "12V Input"}
            ],
            "connections": [
                {"from": "B1", "to": "B2", "label": "Power"}
            ]
        }

    Returns:
        Mermaid diagram syntax string
    """

    # Start Mermaid flowchart
    mermaid = "flowchart TD\n"

    # Map block types to visual styles
    style_classes = {
        'processor': 'processorStyle',
        'power_input': 'powerStyle',
        'power_regulator': 'powerStyle',
        'interface': 'interfaceStyle',
        'memory': 'memoryStyle',
        'analog': 'analogStyle',
        'sensor': 'sensorStyle'
    }

    # Add blocks
    blocks = diagram_json.get('blocks', [])
    for block in blocks:
        block_id = block['id']
        label = block['label'].replace('"', "'")
        block_type = block.get('type', 'default')

        # Choose shape based on type
        if block_type == 'processor':
            # Hexagon for processors
            mermaid += f'    {block_id}["{label}"]{{{{processor}}}}\n'
        elif 'power' in block_type:
            # Rounded box for power
            mermaid += f'    {block_id}("{label}")\n'
        elif block_type == 'interface':
            # Rectangle for interfaces
            mermaid += f'    {block_id}["{label}"]\n'
        else:
            # Default rectangle
            mermaid += f'    {block_id}["{label}"]\n'

    mermaid += "\n"

    # Add connections
    connections = diagram_json.get('connections', [])
    for conn in connections:
        from_id = conn.get('from', '')
        to_id = conn.get('to', '')
        label = conn.get('label', '')

        if from_id and to_id:
            if label:
                label_clean = label.replace('"', "'")
                mermaid += f'    {from_id} -->|"{label_clean}"| {to_id}\n'
            else:
                mermaid += f'    {from_id} --> {to_id}\n'

    mermaid += "\n"

    # Add styling
    mermaid += """
    classDef processorStyle fill:#4A90E2,stroke:#2E5C8A,stroke-width:3px,color:#fff
    classDef powerStyle fill:#F5A623,stroke:#D68910,stroke-width:2px,color:#fff
    classDef interfaceStyle fill:#7ED321,stroke:#5FA319,stroke-width:2px,color:#fff
    classDef memoryStyle fill:#BD10E0,stroke:#9012AB,stroke-width:2px,color:#fff
    classDef analogStyle fill:#50E3C2,stroke:#3AB09E,stroke-width:2px,color:#fff
    classDef sensorStyle fill:#F8E71C,stroke:#C4B616,stroke-width:2px,color:#333
    """

    return mermaid


def mermaid_to_image_url(mermaid_code):
    """
    Convert Mermaid code to image URL using Mermaid.ink service

    Args:
        mermaid_code: Mermaid syntax string

    Returns:
        URL to rendered PNG image
    """
    import base64
    import urllib.parse

    # Encode Mermaid code
    encoded = base64.b64encode(mermaid_code.encode('utf-8')).decode('utf-8')

    # Use Mermaid.ink public API (free)
    image_url = f"https://mermaid.ink/img/{encoded}"

    return image_url


def generate_html_preview(mermaid_code, diagram_json, project_name):
    """
    Generate HTML page with embedded Mermaid diagram for preview

    Returns:
        HTML string that can be saved and opened in browser
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Block Diagram - {project_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4A90E2;
            padding-bottom: 10px;
        }}
        .info {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .diagram {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .buttons {{
            margin: 30px 0;
            display: flex;
            gap: 15px;
        }}
        button {{
            padding: 12px 24px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .approve {{
            background: #28a745;
            color: white;
        }}
        .approve:hover {{
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .reject {{
            background: #dc3545;
            color: white;
        }}
        .reject:hover {{
            background: #c82333;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
        .modify {{
            background: #ffc107;
            color: #333;
        }}
        .modify:hover {{
            background: #e0a800;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔧 Block Diagram Preview</h1>

        <div class="info">
            <strong>Project:</strong> {project_name}<br>
            <strong>System Type:</strong> {diagram_json.get('metadata', {}).get('system_type', 'Unknown')}<br>
            <strong>Generated:</strong> {diagram_json.get('metadata', {}).get('created', 'N/A')}
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value">{len(diagram_json.get('blocks', []))}</div>
                <div class="stat-label">Total Blocks</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{len(diagram_json.get('connections', []))}</div>
                <div class="stat-label">Connections</div>
            </div>
        </div>

        <div class="diagram">
            <div class="mermaid">
{mermaid_code}
            </div>
        </div>

        <div class="buttons">
            <button class="approve" onclick="approve()">✅ APPROVE</button>
            <button class="reject" onclick="reject()">❌ REJECT</button>
            <button class="modify" onclick="modify()">✏️ MODIFY</button>
        </div>

        <div id="response" style="margin-top: 20px; padding: 15px; border-radius: 5px; display: none;"></div>
    </div>

    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});

        function approve() {{
            document.getElementById('response').style.display = 'block';
            document.getElementById('response').style.background = '#d4edda';
            document.getElementById('response').style.color = '#155724';
            document.getElementById('response').innerHTML = '<strong>✅ APPROVED!</strong><br>Copy this text and paste in n8n chat: <strong>APPROVE</strong>';
        }}

        function reject() {{
            const reason = prompt('Why are you rejecting? (optional)');
            document.getElementById('response').style.display = 'block';
            document.getElementById('response').style.background = '#f8d7da';
            document.getElementById('response').style.color = '#721c24';
            document.getElementById('response').innerHTML = '<strong>❌ REJECTED!</strong><br>Copy this text and paste in n8n chat: <strong>REJECT' + (reason ? ': ' + reason : '') + '</strong>';
        }}

        function modify() {{
            const changes = prompt('What changes do you want?');
            document.getElementById('response').style.display = 'block';
            document.getElementById('response').style.background = '#fff3cd';
            document.getElementById('response').style.color = '#856404';
            document.getElementById('response').innerHTML = '<strong>✏️ MODIFY!</strong><br>Copy this text and paste in n8n chat: <strong>MODIFY: ' + (changes || 'Please make changes') + '</strong>';
        }}
    </script>
</body>
</html>
"""

    return html


# Example usage
if __name__ == '__main__':
    # Example block diagram
    example_diagram = {
        "metadata": {
            "project": "Motor_Controller_Test",
            "system_type": "Motor_Control",
            "created": "2026-02-10"
        },
        "blocks": [
            {"id": "B1", "type": "processor", "label": "TMS320F28379D DSP"},
            {"id": "B2", "type": "power_input", "label": "48V DC Input"},
            {"id": "B3", "type": "power_regulator", "label": "5V Regulator"},
            {"id": "B4", "type": "power_regulator", "label": "3.3V Regulator"},
            {"id": "B5", "type": "interface", "label": "CAN Bus"},
            {"id": "B6", "type": "interface", "label": "Ethernet PHY"},
            {"id": "B7", "type": "sensor", "label": "Current Sensor"},
            {"id": "B8", "type": "sensor", "label": "Temperature Sensor"}
        ],
        "connections": [
            {"from": "B2", "to": "B3", "label": "48V"},
            {"from": "B2", "to": "B4", "label": "48V"},
            {"from": "B3", "to": "B1", "label": "5V"},
            {"from": "B4", "to": "B1", "label": "3.3V"},
            {"from": "B1", "to": "B5", "label": "CAN"},
            {"from": "B1", "to": "B6", "label": "RMII"},
            {"from": "B7", "to": "B1", "label": "ADC"},
            {"from": "B8", "to": "B1", "label": "ADC"}
        ]
    }

    # Generate Mermaid code
    mermaid_code = block_diagram_to_mermaid(example_diagram)
    print("Mermaid Code:")
    print(mermaid_code)
    print("\n")

    # Generate image URL
    image_url = mermaid_to_image_url(mermaid_code)
    print(f"Image URL: {image_url}")
    print("\n")

    # Generate HTML preview
    html = generate_html_preview(mermaid_code, example_diagram, "Motor_Controller_Test")

    # Save HTML
    with open('/tmp/block_diagram_preview.html', 'w') as f:
        f.write(html)

    print("HTML preview saved to: /tmp/block_diagram_preview.html")
    print("Open this file in a browser to see the visual diagram!")
