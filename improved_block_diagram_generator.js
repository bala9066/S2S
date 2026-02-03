// ==========================================
// IMPROVED UNIVERSAL BLOCK DIAGRAM GENERATOR
// Supports comprehensive hardware designs
// ==========================================

const parsed = $json.parsed_requirements || {};
const projectName = $json.project_name || 'Hardware_Project';
const systemType = $json.system_type || 'Digital_Controller';

const diagram = {
  version: '2.0',
  type: 'hardware_block_diagram',
  metadata: {
    project: projectName,
    system_type: systemType,
    created: new Date().toISOString(),
    design_complexity: parsed.system_overview?.design_complexity || 'medium'
  },
  blocks: [],
  connections: [],
  power_tree: [],
  signal_domains: []
};

let blockId = 1;
const blockMap = {};

// Helper to create block
function addBlock(type, label, category, position) {
  const block = {
    id: `B${blockId}`,
    type: type,
    label: label,
    category: category,
    position: position || {x: 500, y: 300}
  };
  diagram.blocks.push(block);
  blockMap[type + '_' + label.replace(/\s+/g, '_')] = block.id;
  blockId++;
  return block.id;
}

// Helper to add connection
function addConnection(fromId, toId, label, type = 'signal') {
  diagram.connections.push({
    from: fromId,
    to: toId,
    label: label || '',
    type: type  // signal, power, data, analog, rf
  });
}

// ==========================================
// 1. POWER SYSTEM
// ==========================================
console.log('[DIAGRAM] Building power system...');

const power = parsed.primary_components?.power_system || {};
const inputVoltage = power.input_voltage || '12V';

// Input power block
const inputPowerId = addBlock('power_input', `Input ${inputVoltage}`, 'power', {x: 100, y: 100});

// Protection circuitry
if (power.protection && power.protection.length > 0) {
  const protId = addBlock('protection', 'Protection Circuit', 'power', {x: 250, y: 100});
  addConnection(inputPowerId, protId, inputVoltage, 'power');
  blockMap.protected_input = protId;
}

// Power rails
const rails = power.rails_needed || [{voltage: '3.3V', purpose: 'main'}];
let railY = 200;

rails.forEach((rail, i) => {
  const voltage = rail.voltage || rail;
  const purpose = rail.purpose || 'system';
  const current = rail.current || 'TBD';

  const railId = addBlock(
    'power_regulator',
    `${voltage} @ ${current}`,
    'power',
    {x: 100 + (i % 3) * 120, y: railY + Math.floor(i / 3) * 80}
  );

  const sourceId = blockMap.protected_input || inputPowerId;
  addConnection(sourceId, railId, inputVoltage, 'power');

  // Store rail for later connections
  blockMap[`rail_${voltage.replace('.', 'p')}`] = railId;

  diagram.power_tree.push({
    rail: voltage,
    regulator_id: railId,
    purpose: purpose,
    current: current
  });
});

// ==========================================
// 2. PROCESSOR / MAIN CONTROLLER
// ==========================================
console.log('[DIAGRAM] Adding processor...');

const proc = parsed.primary_components?.processor || {};
const procLabel = proc.specific_part || proc.type || 'MCU';
const procId = addBlock('processor', procLabel, 'processing', {x: 500, y: 300});

// Connect power to processor
const procVoltage = rails.find(r => r.purpose?.includes('core') || r.voltage === '3.3V' || r.voltage === '1.8V');
if (procVoltage) {
  const railId = blockMap[`rail_${procVoltage.voltage.replace('.', 'p')}`];
  if (railId) addConnection(railId, procId, procVoltage.voltage, 'power');
}

// ==========================================
// 3. MEMORY
// ==========================================
const memory = parsed.primary_components?.memory || {};

if (memory.ram_type && memory.ram_type !== 'none') {
  const ramId = addBlock('memory', `${memory.ram_type} ${memory.ram_size || ''}`, 'memory', {x: 700, y: 250});
  addConnection(procId, ramId, 'DDR Interface', 'data');

  // Power for RAM
  const ramVoltage = memory.ram_type.includes('DDR4') ? '1.2V' : '1.5V';
  const ramRailId = blockMap[`rail_${ramVoltage.replace('.', 'p')}`];
  if (ramRailId) addConnection(ramRailId, ramId, ramVoltage, 'power');
}

if (memory.flash_type) {
  const flashId = addBlock('memory', `${memory.flash_type} Flash ${memory.flash_size || ''}`, 'memory', {x: 700, y: 350});
  addConnection(procId, flashId, memory.flash_type.includes('QSPI') ? 'QSPI' : 'SPI', 'data');
}

// ==========================================
// 4. COMMUNICATION INTERFACES
// ==========================================
console.log('[DIAGRAM] Adding interfaces...');

const interfaces = parsed.primary_components?.interfaces_communication || [];
let ifaceY = 150;

interfaces.forEach((iface, i) => {
  const ifaceType = iface.type || iface;
  const ifaceLabel = typeof iface === 'object' ?
    `${iface.type} ${iface.speed || ''}` :
    ifaceType;

  const ifaceId = addBlock(
    'interface',
    ifaceLabel,
    'communication',
    {x: 800, y: ifaceY + i * 70}
  );

  addConnection(procId, ifaceId, ifaceType, 'data');

  // Add PHY if needed
  if (['Ethernet', 'USB', 'CAN'].includes(ifaceType)) {
    const phyId = addBlock('phy', `${ifaceType} PHY`, 'communication', {x: 950, y: ifaceY + i * 70});
    addConnection(ifaceId, phyId, `${ifaceType} signals`, 'signal');

    // External connector
    const connId = addBlock('connector', `${ifaceType} Port`, 'external', {x: 1100, y: ifaceY + i * 70});
    addConnection(phyId, connId, 'Physical', 'signal');
  }
});

// ==========================================
// 5. ANALOG SIGNAL CHAIN (Sensors/ADC/DAC)
// ==========================================
console.log('[DIAGRAM] Adding analog signal chain...');

const analog = parsed.primary_components?.analog_signal_chain || {};

// ADC
if (analog.adc) {
  const adcId = addBlock('adc', `${analog.adc.resolution} ADC`, 'analog', {x: 350, y: 450});
  addConnection(adcId, procId, 'SPI/I2C', 'data');

  // Sensors
  const sensors = analog.sensors || [];
  sensors.forEach((sensor, i) => {
    const sensorId = addBlock(
      'sensor',
      `${sensor.type} Sensor`,
      'sensing',
      {x: 150, y: 450 + i * 60}
    );

    // Signal conditioning
    if (analog.amplifiers && analog.amplifiers.length > 0) {
      const ampId = addBlock('amplifier', 'Signal Conditioning', 'analog', {x: 250, y: 450 + i * 60});
      addConnection(sensorId, ampId, 'Analog', 'analog');
      addConnection(ampId, adcId, 'Conditioned', 'analog');
    } else {
      addConnection(sensorId, adcId, 'Analog', 'analog');
    }
  });
}

// DAC
if (analog.dac) {
  const dacId = addBlock('dac', `${analog.dac.resolution} DAC`, 'analog', {x: 650, y: 450});
  addConnection(procId, dacId, 'SPI/I2C', 'data');
}

// ==========================================
// 6. POWER STAGE (Motor Control, Power Electronics)
// ==========================================
const powerStage = parsed.primary_components?.power_stage || {};

if (powerStage.relevant_for && powerStage.switches) {
  console.log('[DIAGRAM] Adding power stage...');

  // Gate driver
  const gateDriverId = addBlock(
    'gate_driver',
    `Gate Driver (${powerStage.gate_drivers?.channels || 6}ch)`,
    'power_stage',
    {x: 400, y: 600}
  );
  addConnection(procId, gateDriverId, 'PWM Signals', 'signal');

  // Power switches
  const switchType = powerStage.switches.type || 'MOSFET';
  const switchId = addBlock(
    'power_switch',
    `${switchType} (${powerStage.switches.voltage_rating || 'TBD'})`,
    'power_stage',
    {x: 550, y: 600}
  );
  addConnection(gateDriverId, switchId, 'Gate Drive', 'signal');

  // Output stage
  const outputId = addBlock(
    'output_stage',
    powerStage.output_stage || '3-Phase Output',
    'power_stage',
    {x: 700, y: 600}
  );
  addConnection(switchId, outputId, 'Switched Power', 'power');

  // Load
  const loadType = systemType.includes('Motor') ? '3-Phase Motor' : 'Load';
  const loadId = addBlock('load', loadType, 'external', {x: 850, y: 600});
  addConnection(outputId, loadId, 'Output Power', 'power');

  // Current sensing feedback
  const currentSenseId = addBlock('current_sensor', 'Current Sensing', 'sensing', {x: 700, y: 700});
  addConnection(outputId, currentSenseId, 'Current', 'analog');
  addConnection(currentSenseId, procId, 'Feedback', 'analog');
}

// ==========================================
// 7. RF FRONTEND (RF/Wireless systems)
// ==========================================
const rf = parsed.primary_components?.rf_frontend || {};

if (rf.relevant_for && rf.components) {
  console.log('[DIAGRAM] Adding RF frontend...');

  let rfX = 400, rfY = 150;

  rf.components.forEach((comp, i) => {
    const compId = addBlock(
      'rf_component',
      comp.type + (comp.gain ? ` (${comp.gain})` : ''),
      'rf',
      {x: rfX + i * 120, y: rfY}
    );

    if (i === 0) {
      addConnection(procId, compId, 'Control', 'signal');
    } else {
      // Connect RF components in chain
      const prevId = diagram.blocks[diagram.blocks.length - 2].id;
      addConnection(prevId, compId, 'RF Signal', 'rf');
    }

    // Matching networks
    if (rf.matching_networks && rf.matching_networks.length > i) {
      const matchId = addBlock('matching_network', 'Matching Network', 'rf', {x: rfX + i * 120, y: rfY + 60});
      addConnection(compId, matchId, '50Ω', 'rf');
    }
  });

  // Antenna
  const antennaId = addBlock('antenna', 'Antenna', 'external', {x: rfX + rf.components.length * 120, y: rfY});
  const lastRfId = diagram.blocks[diagram.blocks.length - 1].id;
  addConnection(lastRfId, antennaId, 'RF Out', 'rf');
}

// ==========================================
// 8. CLOCKING
// ==========================================
const clocking = parsed.primary_components?.clocking || {};

if (clocking.primary_clock) {
  const clockId = addBlock(
    'clock',
    `${clocking.primary_clock.frequency} ${clocking.primary_clock.source}`,
    'timing',
    {x: 350, y: 250}
  );
  addConnection(clockId, procId, 'Clock', 'signal');
}

// ==========================================
// 9. USER INTERFACE
// ==========================================
const ui = parsed.primary_components?.user_interface || {};

if (ui.display && ui.display.type !== 'none') {
  const displayId = addBlock('display', `${ui.display.type} Display`, 'ui', {x: 650, y: 150});
  addConnection(procId, displayId, 'Display Interface', 'data');
}

if (ui.input && ui.input.length > 0) {
  const inputId = addBlock('user_input', ui.input.join(', '), 'ui', {x: 650, y: 100});
  addConnection(inputId, procId, 'User Input', 'signal');
}

// ==========================================
// 10. STORAGE
// ==========================================
const storage = parsed.primary_components?.storage_logging || {};

if (storage.sd_card === 'yes') {
  const sdId = addBlock('storage', 'SD Card', 'storage', {x: 750, y: 400});
  addConnection(procId, sdId, 'SD/SDIO', 'data');
}

if (storage.eeprom) {
  const eepromId = addBlock('storage', `EEPROM ${storage.eeprom.size}`, 'storage', {x: 750, y: 450});
  addConnection(procId, eepromId, storage.eeprom.interface || 'I2C', 'data');
}

// ==========================================
// GENERATE ASCII DIAGRAM
// ==========================================
console.log(`[DIAGRAM] Generated ${diagram.blocks.length} blocks, ${diagram.connections.length} connections`);

const safeName = (projectName || 'Project').substring(0, 30).padEnd(30);
const safeType = (systemType || 'Unknown').substring(0, 29).padEnd(29);

// Group blocks by category
const blocksByCategory = {};
diagram.blocks.forEach(b => {
  if (!blocksByCategory[b.category]) blocksByCategory[b.category] = [];
  blocksByCategory[b.category].push(b);
});

let componentList = '';
let categoryIndex = 1;

Object.keys(blocksByCategory).sort().forEach(category => {
  componentList += `\n${categoryIndex}. ${category.toUpperCase().replace('_', ' ')}:\n`;
  blocksByCategory[category].forEach((block, i) => {
    componentList += `   ${String.fromCharCode(97 + i)}. ${block.label} [${block.type}]\n`;
  });
  categoryIndex++;
});

const asciiDiagram = `
╔════════════════════════════════════════════╗
║   BLOCK DIAGRAM: ${safeName}  ║
╠════════════════════════════════════════════╣
║   System Type: ${safeType} ║
║   Total Blocks: ${diagram.blocks.length.toString().padEnd(28)}║
║   Connections: ${diagram.connections.length.toString().padEnd(29)}║
║   Power Rails: ${(rails.length || 0).toString().padEnd(29)}║
╚════════════════════════════════════════════╝

SYSTEM ARCHITECTURE:
${componentList}

POWER DISTRIBUTION:
${diagram.power_tree.map((p, i) =>
  `  ${i+1}. ${p.rail} @ ${p.current} → ${p.purpose}`
).join('\n') || '  (Power tree to be generated)'}

CRITICAL SIGNAL PATHS:
${diagram.connections
  .filter(c => c.type !== 'power')
  .slice(0, 10)
  .map((c, i) => {
    const fromBlock = diagram.blocks.find(b => b.id === c.from);
    const toBlock = diagram.blocks.find(b => b.id === c.to);
    return `  ${i+1}. ${fromBlock?.label || 'Unknown'} → [${c.label}] → ${toBlock?.label || 'Unknown'}`;
  }).join('\n')}
${diagram.connections.length > 10 ? `\n  ... and ${diagram.connections.length - 10} more connections` : ''}

DESIGN NOTES:
- Total components identified: ${diagram.blocks.length}
- Power domains: ${new Set(diagram.power_tree.map(p => p.rail)).size}
- Interface types: ${new Set(interfaces.map(i => i.type || i)).size}
- This is a preliminary block diagram for approval
`;

return {
  json: {
    ...($json),
    block_diagram: diagram,
    ascii_diagram: asciiDiagram,
    awaiting_approval: true,
    diagram_stats: {
      total_blocks: diagram.blocks.length,
      total_connections: diagram.connections.length,
      power_rails: rails.length,
      categories: Object.keys(blocksByCategory).length
    }
  }
};
