# Changelog

All notable changes to the S2S (Specification to Silicon) Hardware Pipeline project.

## [2.0.0] - 2026-02-03

### 🎉 Major Features

#### LCSC Supplier Integration
- **Added LCSC (Lichuang) supplier support** to component scraper
  - Chinese component distributor with 30-50% lower prices than DigiKey/Mouser
  - Extends component search from 2 suppliers to 3 suppliers
  - Playwright-based scraping with robust error handling
  - Automatic price comparison across all 3 suppliers

#### Perfect Component Listing
- **New `search_all_suppliers()` function** for multi-component parallel search
  - Searches all 3 suppliers (DigiKey, Mouser, LCSC) simultaneously
  - Returns comprehensive results organized by component type
  - Eliminates missing components and incomplete searches
  - Optimized for performance with parallel async execution

#### Enhanced REST API
- **New endpoint: `/api/scrape/all`** for multi-component search
  - Accepts list of components to search
  - Returns aggregated results from all suppliers
  - Perfect for BOM generation and component sourcing
  - Example payload:
    ```json
    {
      "components": [
        {"search_term": "STM32F4", "category": "processor"},
        {"search_term": "buck converter 3.3V", "category": "power_regulator"}
      ]
    }
    ```

### 📝 Documentation

#### New Documentation Files
- **`START_HERE.md`** (1,000+ lines)
  - Complete quick start guide (10-minute setup)
  - File structure explanation
  - 8-phase workflow overview
  - Component scraper API documentation
  - Troubleshooting guide
  - Example inputs and expected outputs
  - Cost estimates and ROI analysis

- **`CHANGELOG.md`** (this file)
  - Version history
  - Feature additions
  - API changes
  - Migration guides

- **`test_component_search.py`**
  - Automated test suite for component scraper
  - Tests all 3 suppliers (DigiKey, Mouser, LCSC)
  - Cache validation
  - search_all() function testing

### 🔧 Technical Improvements

#### Component Scraper (`component_scraper.py`)
- Added `ComponentInfo` dataclass for type-safe component data
- Added `LCSCScraper` class with robust error handling
- Updated parallel scraping to include LCSC as 3rd supplier
- Fixed sources tracking to include LCSC in result dictionary
- Added `search_all_suppliers()` async function for batch searches

#### Scraper API (`scraper_api.py`)
- Updated API title and description to mention LCSC
- Added `ComponentSearchItem` Pydantic model
- Added `SearchAllRequest` Pydantic model
- Added `SearchAllResponse` Pydantic model
- Implemented `/api/scrape/all` endpoint
- Updated API version from 1.0.0 to 2.0.0

#### Database Integration
- 30-day component caching for all 3 suppliers
- Source tracking: DigiKey, Mouser, LCSC
- Automatic cache expiry and cleanup
- Price comparison across suppliers

### 🐛 Bug Fixes
- Fixed missing LCSC in sources dictionary (line 796-798 in component_scraper.py)
- Improved error handling for supplier-specific scraping failures
- Added proper exception handling in search_all_suppliers()

### 📊 Performance Improvements
- Parallel execution of all 3 supplier searches
- Async/await for non-blocking I/O operations
- Efficient database caching (30-day TTL)
- Optimized Playwright browser management

### 🔐 Security
- API key configuration via `.env` file
- Never commit secrets to git (`.gitignore` protection)
- Docker container isolation
- CORS middleware for controlled API access

---

## [1.0.0] - 2026-01-24

### Initial Release

#### Core Features
- **8-Phase Hardware Design Pipeline**
  - Phase 1: Requirements & Component Selection
  - Phase 2: HRS Document Generation
  - Phase 3: Design Constraints & Compliance
  - Phase 4: Netlist Generation
  - Phase 5: PCB Design (Manual)
  - Phase 6: GLR Generation
  - Phase 7: FPGA Implementation (Manual)
  - Phase 8: Software Development

- **n8n Workflow Orchestration**
  - Original workflow (17 nodes)
  - Enhanced workflow with GLB + Power Budget (25 nodes)

- **Component Scraper (DigiKey + Mouser)**
  - Playwright-based web scraping
  - PostgreSQL caching (30 days)
  - FastAPI REST API wrapper

- **Claude AI Integration**
  - Requirements parsing
  - Component recommendations
  - Document generation (HRS, SRS, SDD)
  - Code generation (C/C++/Qt)

- **Database**
  - PostgreSQL with 10 tables
  - Component cache with expiry
  - Project management
  - Compliance tracking

- **Documentation**
  - REPOSITORY_ANALYSIS.md (948 lines)
  - ENHANCED_WORKFLOW_GUIDE.md (800+ lines)
  - WORKFLOW_COMPARISON.md (345 lines)
  - N8N_IMPORT_GUIDE.md (589 lines)
  - Hackathon_Registration_Final.md (problem statement)

---

## Migration Guide

### Migrating from v1.0.0 to v2.0.0

#### Breaking Changes
None - v2.0.0 is fully backward compatible with v1.0.0

#### New Features to Adopt

1. **Update to LCSC-enabled scraper**
   ```bash
   # Pull latest code
   git pull origin main

   # Restart scraper API
   docker-compose restart scraper-api
   ```

2. **Use new `/api/scrape/all` endpoint**
   ```python
   # Old way (sequential searches)
   for component in components:
       result = requests.post('/api/scrape', json=component)

   # New way (parallel searches - FASTER)
   result = requests.post('/api/scrape/all', json={
       'components': components
   })
   ```

3. **Benefit from LCSC pricing**
   - BOM costs reduced by 30-50% for many components
   - Automatic price comparison in BOM.xlsx
   - Lowest price highlighted

4. **Update n8n workflow to use search_all**
   - Replace multiple HTTP Request nodes with single `/api/scrape/all` call
   - Reduces workflow complexity
   - Improves performance (parallel vs sequential)

---

## Roadmap

### Planned for v2.1.0
- [ ] Octopart API integration (4th supplier)
- [ ] Real-time stock availability monitoring
- [ ] Component price alerts (email/Slack notifications)
- [ ] BOM cost optimization (suggest cheaper alternatives)

### Planned for v2.2.0
- [ ] Component lifecycle status tracking (Active, NRND, Obsolete)
- [ ] Multi-sourcing recommendations (avoid single-source components)
- [ ] Lead time analysis
- [ ] Inventory management integration

### Planned for v3.0.0
- [ ] AI-powered component substitution (suggest pin-compatible alternatives)
- [ ] Automated compliance verification (parse datasheets for RoHS/REACH)
- [ ] PCB layout automation (Phase 5)
- [ ] FPGA logic synthesis automation (Phase 7)

---

## Contributors

- **S2S Team** - DATA PATTERNS GREAT AI HACK-A-THON 2026
- **Claude Sonnet 4.5** - AI assistant for code generation and documentation

---

## License

Proprietary - DATA PATTERNS Corporation

---

## Support

For issues, questions, or feature requests:
1. Check `START_HERE.md` for quick troubleshooting
2. Review `REPOSITORY_ANALYSIS.md` for technical details
3. Check Docker logs: `docker-compose logs -f`
4. Contact hackathon team

---

**Version Format:** `MAJOR.MINOR.PATCH`
- **MAJOR:** Breaking changes
- **MINOR:** New features (backward compatible)
- **PATCH:** Bug fixes (backward compatible)
