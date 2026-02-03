# Contributing to Hardware Pipeline

Thank you for your interest in contributing to Hardware Pipeline! This document provides guidelines and instructions for contributing.

---

## 🤝 How to Contribute

### Reporting Issues

Found a bug or have a feature request? Please open an issue:

1. **Search existing issues** to avoid duplicates
2. **Use issue templates** when available
3. **Provide details:**
   - Clear description of the issue/feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Environment details (OS, Docker version, etc.)
   - Logs or screenshots if applicable

### Submitting Pull Requests

1. **Fork the repository**
   ```bash
   git clone https://github.com/bala9066/S2S.git
   cd S2S
   git checkout -b feature/your-feature-name
   ```

2. **Set up development environment**
   ```bash
   # Copy environment template
   cp .env.example .env
   # Edit .env with your API keys

   # Install dependencies
   pip install -r requirements.txt
   pip install playwright
   playwright install chromium
   ```

3. **Make your changes**
   - Follow code style guidelines (see below)
   - Add tests if applicable
   - Update documentation
   - Keep commits atomic and well-described

4. **Test your changes**
   ```bash
   # Run linting
   flake8 *.py

   # Run type checking
   mypy *.py

   # Test the scraper
   python component_scraper.py "STM32F4" "processor"

   # Test the API
   python scraper_api.py
   # In another terminal:
   curl http://localhost:8000/api/health
   ```

5. **Submit Pull Request**
   - Push to your fork
   - Open PR against `main` branch
   - Fill in PR template with:
     - Description of changes
     - Related issues (if any)
     - Testing performed
     - Screenshots (if UI changes)

---

## 📝 Code Style Guidelines

### Python

Follow **PEP 8** with these specifics:

```python
# Use type hints
def scrape_components(search_term: str, category: str) -> Dict[str, Any]:
    """Docstring with clear description.

    Args:
        search_term: What to search for
        category: Component category

    Returns:
        Dictionary with scraped components
    """
    pass

# Use meaningful variable names
component_count = len(components)  # Good
cc = len(c)                        # Bad

# Keep functions focused and small
# Max 50 lines per function (guideline, not strict rule)

# Use f-strings for formatting
message = f"Found {count} components"  # Good
message = "Found {} components".format(count)  # Acceptable
message = "Found " + str(count) + " components"  # Avoid
```

**Tools:**
- `black` for formatting: `black *.py`
- `flake8` for linting: `flake8 *.py`
- `mypy` for type checking: `mypy *.py`

### SQL

Follow **PostgreSQL conventions:**

```sql
-- Use uppercase for keywords
SELECT part_number, manufacturer
FROM component_cache
WHERE lifecycle_status = 'Active'
ORDER BY cached_at DESC;

-- Use meaningful aliases
SELECT
    cc.part_number,
    p.project_name
FROM component_cache AS cc
JOIN projects AS p ON cc.project_id = p.id;

-- Add comments for complex queries
-- Find active components cached in the last 7 days
SELECT * FROM component_cache
WHERE expires_at > NOW()
  AND cached_at > NOW() - INTERVAL '7 days';
```

### JavaScript/n8n

```javascript
// Use const/let, not var
const searchTerm = $json.search_term;
let results = [];

// Use arrow functions
const processComponent = (comp) => {
    return {
        part: comp.part_number,
        price: comp.pricing.unit_price
    };
};

// Add comments for complex logic
// Calculate weighted score based on price, availability, and lifecycle
const score = (comp.price_score * 0.4) +
              (comp.availability_score * 0.3) +
              (comp.lifecycle_score * 0.3);
```

### Markdown

```markdown
# Use ATX-style headers

## Second level

- Use dashes for unordered lists
- Not asterisks

1. Use numbers for ordered lists
2. Even if you number them all as 1

**Bold** for emphasis, *italic* for slight emphasis

`inline code` for short code snippets

\`\`\`python
# Code blocks with language
def example():
    pass
\`\`\`
```

---

## 🧪 Testing

### Manual Testing

Before submitting, test your changes:

```bash
# Start services
docker compose up -d

# Test Phase 1 workflow with all system types
# 1. RF/Wireless
# 2. Motor Control
# 3. Digital Controller
# 4. Power Electronics
# 5. Industrial Control
# 6. Sensor System

# Check logs for errors
docker compose logs -f n8n
docker compose logs -f playwright

# Stop services
docker compose down
```

### Automated Tests (TODO)

We're building a test suite. Contributions welcome!

```python
# tests/test_component_scraper.py
import pytest
from component_scraper import scrape_components

@pytest.mark.asyncio
async def test_scrape_basic():
    """Test basic component scraping"""
    result = await scrape_components("STM32F4", "processor")
    assert result['success'] == True
    assert len(result['components']) > 0

# Run with: pytest tests/
```

---

## 📚 Documentation

### Code Documentation

```python
def complex_function(param1: str, param2: int) -> Dict[str, Any]:
    """One-line summary of what the function does.

    More detailed explanation if needed. Explain the "why"
    not just the "what".

    Args:
        param1: Description of first parameter
        param2: Description of second parameter

    Returns:
        Dictionary containing:
            - key1: Description
            - key2: Description

    Raises:
        ValueError: When param2 is negative
        ConnectionError: When database is unreachable

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result['key1'])
        'expected output'
    """
    pass
```

### Markdown Documentation

- **Update README.md** if adding major features
- **Add inline comments** for complex logic
- **Document breaking changes** in PR description
- **Include examples** for new features

---

## 🔒 Security

### Reporting Security Issues

**DO NOT** open public issues for security vulnerabilities.

Instead:
1. Email: security@datapatterns.com
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We'll respond within 48 hours.

### Security Guidelines

```python
# ❌ NEVER commit secrets
CLAUDE_API_KEY = "sk-ant-api03-..."  # Bad!

# ✅ Use environment variables
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY")

# ❌ Don't log sensitive data
logger.info(f"API key: {api_key}")  # Bad!

# ✅ Log safely
logger.info("API key configured: ***")

# ❌ Don't expose internal paths
error_msg = f"File not found: /home/user/.secrets/key.txt"

# ✅ Use relative paths
error_msg = "Configuration file not found"
```

### Database Security

```sql
-- ❌ Never use string concatenation
query = f"SELECT * FROM users WHERE username = '{username}'"

-- ✅ Use parameterized queries
cursor.execute(
    "SELECT * FROM users WHERE username = %s",
    (username,)
)
```

---

## 🌳 Branch Strategy

```
main (production-ready)
  ↓
develop (integration branch)
  ↓
feature/your-feature (your work)
```

### Branch Naming

- `feature/component-scraper-improvements`
- `bugfix/playwright-timeout-issue`
- `docs/update-readme`
- `hotfix/critical-security-fix`

### Commit Messages

Follow **Conventional Commits:**

```
feat: add support for Mouser API scraping
^--^  ^-----------------------------^
│     │
│     └─⫸ Summary (imperative, lowercase, no period)
│
└──⫸ Type: feat, fix, docs, style, refactor, test, chore
```

**Examples:**
```
feat: add GLM-4 as alternative AI provider
fix: handle playwright timeout gracefully
docs: update deployment guide with troubleshooting
refactor: optimize database query performance
test: add unit tests for component_scraper
chore: update dependencies to latest versions
```

---

## 🎯 Areas for Contribution

### High Priority

1. **Automated Testing**
   - Unit tests for scrapers
   - Integration tests for workflows
   - End-to-end tests for full pipeline

2. **Phase 2 Implementation**
   - PCB layout automation (Phase 5)
   - FPGA HDL generation (Phase 7)
   - Machine learning for recommendations

3. **Performance Optimization**
   - Scraper speed improvements
   - Database query optimization
   - Caching strategies

### Medium Priority

1. **Additional Component Sources**
   - Arrow Electronics
   - Newark/Farnell
   - Manufacturer direct sites

2. **UI Improvements**
   - React frontend for workflow interaction
   - Real-time progress visualization
   - Component comparison interface

3. **Documentation**
   - Video tutorials
   - API documentation improvements
   - More example projects

### Nice to Have

1. **Multi-language Support**
   - Internationalization (i18n)
   - Multiple AI providers for different languages

2. **Advanced Features**
   - Design version control
   - Collaboration features
   - Cloud deployment option

---

## 📞 Getting Help

Stuck? Need clarification?

- **Discord:** [Join our server](https://discord.gg/hardwarepipeline)
- **GitHub Discussions:** [Start a discussion](https://github.com/bala9066/S2S/discussions)
- **Email:** contributors@datapatterns.com

---

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Age, body size, disability, ethnicity
- Gender identity and expression
- Level of experience, education
- Nationality, personal appearance, race, religion
- Sexual identity and orientation

### Our Standards

**Positive behavior:**
- ✅ Using welcoming and inclusive language
- ✅ Being respectful of differing viewpoints
- ✅ Gracefully accepting constructive criticism
- ✅ Focusing on what's best for the community

**Unacceptable behavior:**
- ❌ Trolling, insulting/derogatory comments, personal attacks
- ❌ Public or private harassment
- ❌ Publishing others' private information
- ❌ Other conduct inappropriate in professional settings

### Enforcement

Violations can be reported to: conduct@datapatterns.com

All reports will be reviewed and investigated promptly and fairly.

---

## 🏆 Recognition

Contributors will be:
- Listed in README.md acknowledgments
- Credited in release notes
- Invited to contributor events (when applicable)

Top contributors may receive:
- Direct commit access
- Maintainer status
- Hardware Pipeline swag

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

See [LICENSE](LICENSE) for details.

---

## 🙏 Thank You!

Every contribution, no matter how small, helps make Hardware Pipeline better!

- **Report bugs** → Improve stability
- **Suggest features** → Drive innovation
- **Write docs** → Help others learn
- **Submit code** → Add capabilities

**Let's build the future of hardware design together!** 🚀

---

Questions? Feedback? Reach out: contributors@datapatterns.com
