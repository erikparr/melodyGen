# Procedural Modules Architecture

## Overview

This document outlines the architecture for a **procedural module system** that enables custom, real-time processing of melodies and chords during playback. Modules are self-contained, reusable units that can manipulate melody data, intercept OSC messages, and trigger custom behaviors.

---

## 1. Core Concepts

### 1.1 Module
A **module** is a self-contained directory containing code and configuration that defines a reusable melody processing behavior. Examples:
- Algorithmic note transformation
- Generative rhythm modification
- Conditional OSC routing
- Real-time harmonization
- Dynamic velocity curves

### 1.2 Process
A **process** is a runtime instance of a module, configured with specific parameters and associated with a specific melody/chord object. Multiple processes can be created from the same module with different settings.

### 1.3 Lifecycle
Processes have a clear lifecycle:
- **Create**: Instantiate from module with configuration
- **Attach**: Associate with melody/chord object
- **Activate**: Begin listening/processing (when melody plays)
- **Deactivate**: Stop processing (when melody stops)
- **Detach**: Remove association
- **Destroy**: Clean up resources

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │ ActiveMelodyViewer  │    │   ProceduralView         │   │
│  │  - Melody View      │◄───┤   - Module Browser       │   │
│  │  - Procedural View  │    │   - Process Manager      │   │
│  └─────────────────────┘    │   - Configuration UI     │   │
│                              └──────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Module Runtime (JavaScript)                  │   │
│  │  - Process Registry                                  │   │
│  │  - Lifecycle Manager                                 │   │
│  │  - OSC Interceptor                                   │   │
│  │  - Melody Data Proxy                                 │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/WebSocket
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (Python)                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │      Module Service (Optional Python Modules)       │   │
│  │  - Advanced music21 processing                      │   │
│  │  - Complex transformations                          │   │
│  │  - AI/ML-based generation                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ OSC (7000/7001)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   SuperCollider                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Module Location & Structure

**Modules Directory:**
```
melodyGen/
  modules/                    # Root modules directory
    template/                 # Starter template for new modules
      manifest.json
      index.js
      README.md
    arpeggiator/              # Example module
      manifest.json
      index.js
      ui.jsx                  # Optional UI component
      README.md
    note-randomizer/
      manifest.json
      index.js
    python-transform/         # Hybrid module example
      manifest.json
      index.js                # Frontend entry
      backend.py              # Python processing
```

---

## 3. Module Structure

### 3.1 Module Manifest (`manifest.json`)

```json
{
  "id": "arpeggiator",
  "name": "Arpeggiator",
  "version": "1.0.0",
  "description": "Converts chords into arpeggiated sequences",
  "author": "Your Name",
  "type": "frontend",
  "entryPoint": "index.js",
  "hasUI": true,
  "uiComponent": "ui.jsx",
  "category": "transformation",
  "capabilities": [
    "modify-melody",
    "intercept-osc",
    "send-osc"
  ],
  "parameters": [
    {
      "id": "direction",
      "name": "Direction",
      "type": "select",
      "options": ["up", "down", "updown", "random"],
      "default": "up"
    },
    {
      "id": "rate",
      "name": "Rate (notes per beat)",
      "type": "number",
      "min": 1,
      "max": 16,
      "default": 4
    }
  ]
}
```

### 3.2 Module Entry Point (`index.js`)

**Base Module API:**

```javascript
/**
 * Base class for all procedural modules
 */
class ProceduralModule {
  constructor(config) {
    this.config = config;
    this.melody = null;
    this.track = null;
    this.isActive = false;
  }

  /**
   * Called when process is created
   * @param {Object} processConfig - User-defined parameters
   */
  async onInit(processConfig) {
    // Override in subclass
  }

  /**
   * Called when melody is attached to process
   * @param {Object} melody - Melody data
   * @param {Object} track - Track data
   */
  async onAttach(melody, track) {
    this.melody = melody;
    this.track = track;
  }

  /**
   * Called when melody playback starts
   * @param {Object} context - Playback context
   */
  async onPlay(context) {
    this.isActive = true;
  }

  /**
   * Called when melody playback stops
   */
  async onStop() {
    this.isActive = false;
  }

  /**
   * Called when OSC message is about to be sent
   * @param {Object} oscPayload - OSC payload (can be modified)
   * @returns {Object} Modified payload or null to cancel send
   */
  async onBeforeSendOSC(oscPayload) {
    return oscPayload; // Return modified or original
  }

  /**
   * Called when OSC completion message received
   * @param {Object} completionEvent - Completion event data
   */
  async onOSCComplete(completionEvent) {
    // Override in subclass
  }

  /**
   * Called when melody data changes
   * @param {Object} melody - Updated melody
   */
  async onMelodyChange(melody) {
    this.melody = melody;
  }

  /**
   * Called when process is destroyed
   */
  async onDestroy() {
    // Cleanup
  }

  // --- Helper Methods ---

  /**
   * Modify melody notes
   * @param {Function} transformer - Function to transform notes array
   */
  modifyNotes(transformer) {
    if (!this.melody) return;
    this.melody.notes = transformer(this.melody.notes);
    this.notifyChange();
  }

  /**
   * Send custom OSC message
   * @param {Object} payload - OSC payload
   */
  async sendOSC(payload) {
    // Implementation provided by runtime
  }

  /**
   * Notify system that melody data changed
   */
  notifyChange() {
    // Implementation provided by runtime
  }

  /**
   * Get track index
   */
  getTrackIndex() {
    return this.track?.targetGroup || 0;
  }

  /**
   * Get OSC type (melody or chord)
   */
  getOSCType() {
    return this.track?.oscType || 'melody';
  }
}

export default ProceduralModule;
```

**Example Module Implementation:**

```javascript
// modules/arpeggiator/index.js
import ProceduralModule from '../base/ProceduralModule.js';

class Arpeggiator extends ProceduralModule {
  async onInit(config) {
    this.direction = config.direction || 'up';
    this.rate = config.rate || 4;
  }

  async onBeforeSendOSC(oscPayload) {
    // If this is a chord, arpeggiate it
    if (oscPayload.metadata.chordMode) {
      return this.arpeggiate(oscPayload);
    }
    return oscPayload;
  }

  arpeggiate(payload) {
    const notes = [...payload.notes];
    const arpeggiated = [];

    // Sort notes by pitch based on direction
    if (this.direction === 'up') {
      notes.sort((a, b) => a.midi - b.midi);
    } else if (this.direction === 'down') {
      notes.sort((a, b) => b.midi - a.midi);
    }

    // Convert simultaneous notes to sequence
    const noteDuration = 1 / this.rate;
    notes.forEach((note, i) => {
      arpeggiated.push({
        ...note,
        dur: noteDuration,
        time: i * noteDuration
      });
    });

    return {
      ...payload,
      notes: arpeggiated,
      metadata: {
        ...payload.metadata,
        chordMode: false, // Now sequential
        totalDuration: arpeggiated.length * noteDuration
      }
    };
  }
}

export default Arpeggiator;
```

---

## 4. Process Management

### 4.1 Process Data Structure

```javascript
{
  id: "process_1234567890",
  moduleId: "arpeggiator",
  name: "Fast Upward Arp",
  config: {
    direction: "up",
    rate: 8
  },
  attachments: [
    {
      trackId: "track_abc",
      melodyId: "melody_xyz"
    }
  ],
  enabled: true,
  created: "2025-01-15T10:30:00Z",
  modified: "2025-01-15T11:00:00Z"
}
```

### 4.2 Process Storage

**File-based persistence:**
```
melodyGen/
  processes/
    processes.json          # All process instances
    process_123.state       # Optional: per-process state
```

**processes.json:**
```json
{
  "version": "1.0.0",
  "processes": [
    {
      "id": "process_001",
      "moduleId": "arpeggiator",
      "name": "Fast Arp",
      "config": { "direction": "up", "rate": 8 },
      "attachments": [
        { "trackId": "track_1", "melodyId": "melody_1" }
      ],
      "enabled": true
    }
  ]
}
```

### 4.3 Process Registry (Frontend)

```javascript
// frontend/src/modules/ProcessRegistry.js
class ProcessRegistry {
  constructor() {
    this.modules = new Map();     // moduleId -> Module class
    this.processes = new Map();   // processId -> Process instance
    this.attachments = new Map(); // melodyId -> [processIds]
  }

  registerModule(moduleId, ModuleClass) {
    this.modules.set(moduleId, ModuleClass);
  }

  async createProcess(moduleId, config) {
    const ModuleClass = this.modules.get(moduleId);
    if (!ModuleClass) throw new Error(`Module ${moduleId} not found`);

    const processId = `process_${Date.now()}`;
    const instance = new ModuleClass(config);
    await instance.onInit(config);

    this.processes.set(processId, {
      id: processId,
      moduleId,
      instance,
      config,
      attachments: []
    });

    return processId;
  }

  async attachProcess(processId, melody, track) {
    const process = this.processes.get(processId);
    if (!process) throw new Error(`Process ${processId} not found`);

    await process.instance.onAttach(melody, track);
    process.attachments.push({
      trackId: track.id,
      melodyId: melody.id
    });

    // Index by melody for quick lookup
    if (!this.attachments.has(melody.id)) {
      this.attachments.set(melody.id, []);
    }
    this.attachments.get(melody.id).push(processId);
  }

  getProcessesForMelody(melodyId) {
    const processIds = this.attachments.get(melodyId) || [];
    return processIds.map(id => this.processes.get(id));
  }

  async destroyProcess(processId) {
    const process = this.processes.get(processId);
    if (!process) return;

    await process.instance.onDestroy();

    // Remove from attachments
    process.attachments.forEach(({ melodyId }) => {
      const list = this.attachments.get(melodyId);
      if (list) {
        const idx = list.indexOf(processId);
        if (idx >= 0) list.splice(idx, 1);
      }
    });

    this.processes.delete(processId);
  }
}

export default new ProcessRegistry();
```

---

## 5. Runtime Integration

### 5.1 Playback Hooks

**Modify oscSender.js to support process interception:**

```javascript
// frontend/src/utils/oscSender.js
import ProcessRegistry from '../modules/ProcessRegistry';

export async function sendMelodyToLayer(melody, layer, loop, targetGroup, oscType) {
  // 1. Build base OSC payload
  let oscPayload = convertToOSCFormat(melody, loop, targetGroup, oscType);

  // 2. Get all processes attached to this melody
  const processes = ProcessRegistry.getProcessesForMelody(melody.id);

  // 3. Trigger onPlay for all processes
  const context = { layer, loop, targetGroup, oscType };
  await Promise.all(
    processes.map(p => p.instance.onPlay(context))
  );

  // 4. Apply process transformations via onBeforeSendOSC
  for (const process of processes) {
    if (!process.enabled) continue;

    const modified = await process.instance.onBeforeSendOSC(oscPayload);

    // Process can return null to cancel send
    if (modified === null) {
      console.log(`Process ${process.id} cancelled OSC send`);
      return;
    }

    oscPayload = modified;
  }

  // 5. Send to backend
  const response = await fetch('http://localhost:8000/osc/send-melody', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(oscPayload)
  });

  return response.json();
}
```

### 5.2 OSC Completion Handling

**Extend useSequencer.js and useMultiTrackPlayer.js:**

```javascript
// In WebSocket message handler
socket.onmessage = async (event) => {
  const completionEvent = JSON.parse(event.data);

  // Notify processes
  const melody = getCurrentlyPlayingMelody(completionEvent.targetGroup);
  if (melody) {
    const processes = ProcessRegistry.getProcessesForMelody(melody.id);
    await Promise.all(
      processes.map(p => p.instance.onOSCComplete(completionEvent))
    );
  }

  // ... existing completion handling
};
```

---

## 6. UI Components

### 6.1 View Mode Switcher

**Add to ActiveMelodyViewer.jsx:**

```javascript
const [viewMode, setViewMode] = useState('melody'); // 'melody' | 'procedural'

<div className="view-mode-tabs">
  <button
    className={viewMode === 'melody' ? 'active' : ''}
    onClick={() => setViewMode('melody')}
  >
    Melody View
  </button>
  <button
    className={viewMode === 'procedural' ? 'active' : ''}
    onClick={() => setViewMode('procedural')}
  >
    Procedural View
  </button>
</div>

{viewMode === 'melody' && <MelodyViewer melody={activeMelody} />}
{viewMode === 'procedural' && <ProceduralView melody={activeMelody} />}
```

### 6.2 Procedural View Component

```javascript
// frontend/src/components/ProceduralView.jsx
function ProceduralView({ melody }) {
  const [selectedModule, setSelectedModule] = useState(null);
  const [processes, setProcesses] = useState([]);
  const [availableModules, setAvailableModules] = useState([]);

  useEffect(() => {
    loadAvailableModules();
    loadProcesses();
  }, []);

  return (
    <div className="procedural-view">
      <div className="module-browser">
        <h3>Available Modules</h3>
        <button onClick={generateNewModule}>+ New Module</button>

        <div className="module-list">
          {availableModules.map(module => (
            <ModuleCard
              key={module.id}
              module={module}
              onSelect={setSelectedModule}
            />
          ))}
        </div>
      </div>

      <div className="process-manager">
        <h3>Active Processes</h3>
        {melody && (
          <button onClick={() => createProcess(selectedModule, melody)}>
            + Create Process from {selectedModule?.name}
          </button>
        )}

        <div className="process-list">
          {processes.map(process => (
            <ProcessCard
              key={process.id}
              process={process}
              onConfigure={configureProcess}
              onDelete={deleteProcess}
              onToggle={toggleProcess}
            />
          ))}
        </div>
      </div>

      <div className="process-config">
        {selectedModule && (
          <ModuleConfigPanel module={selectedModule} />
        )}
      </div>
    </div>
  );
}
```

### 6.3 Module Generator

**Endpoint to create new module from template:**

```javascript
async function generateNewModule(name, category) {
  const response = await fetch('http://localhost:8000/modules/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      category,
      template: 'basic' // or 'advanced', 'python-hybrid'
    })
  });

  const { moduleId, path } = await response.json();

  // Open in editor (if possible via system command)
  console.log(`New module created at: ${path}`);

  return moduleId;
}
```

---

## 7. Backend Support

### 7.1 Module API Endpoints

```python
# src/backend/main.py

from fastapi import APIRouter
import os
import json
from pathlib import Path

modules_router = APIRouter(prefix="/modules", tags=["modules"])

@modules_router.get("/list")
async def list_modules():
    """List all available modules"""
    modules_dir = Path("modules")
    modules = []

    for module_path in modules_dir.iterdir():
        if module_path.is_dir():
            manifest_path = module_path / "manifest.json"
            if manifest_path.exists():
                with open(manifest_path) as f:
                    manifest = json.load(f)
                    modules.append({
                        **manifest,
                        "path": str(module_path)
                    })

    return {"modules": modules}

@modules_router.post("/generate")
async def generate_module(request: dict):
    """Generate a new module from template"""
    name = request.get("name")
    category = request.get("category", "general")
    template = request.get("template", "basic")

    # Create module directory
    module_id = name.lower().replace(" ", "-")
    module_path = Path("modules") / module_id
    module_path.mkdir(parents=True, exist_ok=True)

    # Copy template files
    template_path = Path("modules/template")
    # ... copy files and customize

    return {
        "moduleId": module_id,
        "path": str(module_path)
    }

@modules_router.get("/{module_id}/manifest")
async def get_module_manifest(module_id: str):
    """Get module manifest"""
    manifest_path = Path("modules") / module_id / "manifest.json"
    with open(manifest_path) as f:
        return json.load(f)

app.include_router(modules_router)
```

### 7.2 Process Persistence API

```python
@modules_router.get("/processes")
async def list_processes():
    """List all process instances"""
    processes_file = Path("processes/processes.json")
    if processes_file.exists():
        with open(processes_file) as f:
            return json.load(f)
    return {"processes": []}

@modules_router.post("/processes")
async def save_processes(processes: dict):
    """Save process instances"""
    processes_file = Path("processes/processes.json")
    processes_file.parent.mkdir(exist_ok=True)

    with open(processes_file, 'w') as f:
        json.dump(processes, f, indent=2)

    return {"success": True}
```

---

## 8. Module Discovery & Loading

### 8.1 Module Loader (Frontend)

```javascript
// frontend/src/modules/ModuleLoader.js
import ProcessRegistry from './ProcessRegistry';

class ModuleLoader {
  async loadAllModules() {
    // Fetch module list from backend
    const response = await fetch('http://localhost:8000/modules/list');
    const { modules } = await response.json();

    // Dynamically import each module
    for (const moduleMeta of modules) {
      await this.loadModule(moduleMeta);
    }
  }

  async loadModule(moduleMeta) {
    try {
      // Dynamic import (requires module files to be in public/ or served)
      const moduleUrl = `/modules/${moduleMeta.id}/index.js`;
      const module = await import(moduleUrl);

      ProcessRegistry.registerModule(moduleMeta.id, module.default);

      console.log(`✅ Loaded module: ${moduleMeta.name}`);
    } catch (error) {
      console.error(`Failed to load module ${moduleMeta.id}:`, error);
    }
  }
}

export default new ModuleLoader();
```

### 8.2 Initialization in App.jsx

```javascript
// frontend/src/App.jsx
import ModuleLoader from './modules/ModuleLoader';

function App() {
  useEffect(() => {
    // Load modules on startup
    ModuleLoader.loadAllModules();
  }, []);

  // ... rest of app
}
```

---

## 9. Example Use Cases

### 9.1 Real-time Velocity Modifier

```javascript
class VelocityModulator extends ProceduralModule {
  async onInit(config) {
    this.curve = config.curve || 'linear'; // linear, exponential, random
    this.intensity = config.intensity || 0.5;
  }

  async onBeforeSendOSC(oscPayload) {
    const modified = { ...oscPayload };

    modified.notes = oscPayload.notes.map((note, i) => {
      let vel = note.vel;

      switch(this.curve) {
        case 'exponential':
          vel *= Math.pow(i / oscPayload.notes.length, 2);
          break;
        case 'random':
          vel *= 0.5 + Math.random() * 0.5;
          break;
      }

      return { ...note, vel: Math.max(0.1, Math.min(1.0, vel)) };
    });

    return modified;
  }
}
```

### 9.2 Generative Note Addition

```javascript
class GenerativeAdder extends ProceduralModule {
  async onBeforeSendOSC(oscPayload) {
    const notes = [...oscPayload.notes];
    const scale = [0, 2, 4, 5, 7, 9, 11]; // C major

    // Add random notes between existing notes
    notes.forEach((note, i) => {
      if (Math.random() < 0.3) { // 30% chance
        const rootNote = note.midi % 12;
        const scaleDegree = scale[Math.floor(Math.random() * scale.length)];
        const newNote = {
          midi: note.midi - rootNote + scaleDegree,
          vel: note.vel * 0.5,
          dur: note.dur * 0.5,
          time: note.time + note.dur * 0.5
        };
        notes.push(newNote);
      }
    });

    notes.sort((a, b) => a.time - b.time);

    return { ...oscPayload, notes };
  }
}
```

### 9.3 Conditional OSC Router

```javascript
class ConditionalRouter extends ProceduralModule {
  async onInit(config) {
    this.condition = config.condition; // 'pitch-high', 'pitch-low', 'fast', 'slow'
    this.targetGroup = config.targetGroup || 1;
  }

  async onBeforeSendOSC(oscPayload) {
    const avgPitch = oscPayload.notes.reduce((sum, n) => sum + n.midi, 0) / oscPayload.notes.length;

    let shouldReroute = false;

    if (this.condition === 'pitch-high' && avgPitch > 72) {
      shouldReroute = true;
    } else if (this.condition === 'pitch-low' && avgPitch < 60) {
      shouldReroute = true;
    }

    if (shouldReroute) {
      return {
        ...oscPayload,
        metadata: {
          ...oscPayload.metadata,
          targetGroup: this.targetGroup
        }
      };
    }

    return oscPayload;
  }
}
```

---

## 10. Implementation Phases

### Phase 1: Foundation (Week 1)
- [ ] Create module directory structure
- [ ] Implement base ProceduralModule class
- [ ] Create ProcessRegistry
- [ ] Build module template
- [ ] Add backend /modules endpoints

### Phase 2: UI Integration (Week 2)
- [ ] Add view mode switcher to ActiveMelodyViewer
- [ ] Build ProceduralView component
- [ ] Create ModuleBrowser and ProcessManager UI
- [ ] Implement module loading system
- [ ] Add process creation/deletion UI

### Phase 3: Runtime Hooks (Week 3)
- [ ] Integrate process hooks into oscSender
- [ ] Add onPlay/onStop lifecycle triggers
- [ ] Implement OSC interception pipeline
- [ ] Add completion event routing to processes
- [ ] Build process persistence (save/load)

### Phase 4: Module Development (Week 4)
- [ ] Create starter modules (arpeggiator, velocity mod, etc.)
- [ ] Build module generator tool
- [ ] Write module development documentation
- [ ] Add module hot-reload support
- [ ] Create debugging/logging tools

### Phase 5: Advanced Features (Future)
- [ ] Python hybrid modules (frontend + backend processing)
- [ ] Module marketplace/sharing
- [ ] Visual node-based module editor
- [ ] Module chaining/composition
- [ ] State persistence per process instance

---

## 11. Security & Safety Considerations

### 11.1 Sandboxing
- Modules run in same JavaScript context (no true sandboxing)
- Consider adding permissions system (which APIs modules can access)
- Validate module manifests before loading

### 11.2 Error Handling
- Wrap all module callbacks in try-catch
- Provide fallback behavior if module crashes
- Log errors without breaking playback

### 11.3 Performance
- Set timeouts for module operations
- Monitor CPU usage of processes
- Allow disabling processes that cause performance issues

---

## 12. File Structure Summary

```
melodyGen/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── ActiveMelodyViewer.jsx     # Add view mode switcher
│       │   ├── ProceduralView.jsx         # NEW
│       │   ├── ModuleBrowser.jsx          # NEW
│       │   ├── ProcessManager.jsx         # NEW
│       │   └── ProcessConfigPanel.jsx     # NEW
│       ├── modules/
│       │   ├── base/
│       │   │   └── ProceduralModule.js    # NEW - Base class
│       │   ├── ProcessRegistry.js         # NEW
│       │   └── ModuleLoader.js            # NEW
│       └── utils/
│           └── oscSender.js               # MODIFY - Add hooks
├── src/backend/
│   └── main.py                            # ADD /modules endpoints
├── modules/                               # NEW - Module directory
│   ├── template/
│   ├── arpeggiator/
│   ├── velocity-modulator/
│   └── generative-adder/
├── processes/                             # NEW - Process instances
│   └── processes.json
└── PROCEDURAL_MODULES_ARCHITECTURE.md     # This document
```

---

## 13. Open Questions & Design Decisions

### Q1: Frontend-only vs Hybrid Modules?
**Decision needed**: Should we support Python modules from the start, or start frontend-only?
- **Option A**: Frontend-only (simpler, faster to implement)
- **Option B**: Hybrid from start (more powerful, more complex)
- **Recommendation**: Start frontend-only, add Python support in Phase 5

### Q2: Module Installation
**Decision needed**: How do users install third-party modules?
- **Option A**: Manual file copy to modules/ directory
- **Option B**: Module package manager (npm-style)
- **Option C**: Git submodules
- **Recommendation**: Start with Option A, add Option B later

### Q3: UI in Modules
**Decision needed**: Should modules provide custom UI components?
- **Option A**: Parameter-based config only (auto-generate UI)
- **Option B**: Modules can provide React components
- **Recommendation**: Start with A, add B in Phase 4

### Q4: Process-Melody Relationship
**Decision needed**: Can one process attach to multiple melodies?
- **Current spec**: Yes, via attachments array
- **Alternative**: One process per melody (simpler, more process instances)
- **Recommendation**: Keep multi-attachment capability

---

## Conclusion

This architecture provides a powerful, extensible system for real-time melody processing while maintaining clean separation of concerns. The module system is self-contained, discoverable, and integrates seamlessly with the existing MelodyGen architecture.

**Key Benefits:**
- ✅ Self-contained, reusable modules
- ✅ Real-time processing during playback
- ✅ Clean lifecycle management
- ✅ Extensible without core changes
- ✅ File-based persistence
- ✅ Future-proof for advanced features

**Next Steps:**
1. Review and approve architecture
2. Begin Phase 1 implementation
3. Create first example module
4. Document module development API
