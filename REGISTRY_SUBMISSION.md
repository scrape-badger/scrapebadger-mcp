# MCP Registry Submission Guide

This guide explains how to submit the ScrapeBadger MCP server to various registries and directories to maximize discoverability by AI agents and developers.

---

## Table of Contents

1. [Official MCP Registry](#1-official-mcp-registry)
2. [PyPI (Python Package Index)](#2-pypi-python-package-index)
3. [GitHub Repository Setup](#3-github-repository-setup)
4. [Community Directories](#4-community-directories)
5. [Marketing & Promotion](#5-marketing--promotion)

---

## 1. Official MCP Registry

The [MCP Registry](https://registry.modelcontextprotocol.io) is the primary discovery mechanism for MCP servers. This is the most important registration.

### Prerequisites

- Package must be published to a package registry (PyPI, npm, or DockerHub)
- GitHub repository must be public
- Namespace ownership must be verified

### Step 1: Install MCP CLI

```bash
npm install -g @anthropic/mcp-cli
# or
npx @anthropic/mcp-cli
```

### Step 2: Authenticate

```bash
mcp auth login
# Follow the prompts to authenticate with GitHub
```

### Step 3: Create server.json

Create a `server.json` file in your repository root:

```json
{
  "$schema": "https://registry.modelcontextprotocol.io/schemas/server.json",
  "name": "scrapebadger",
  "displayName": "ScrapeBadger",
  "description": "Twitter/X scraping API for AI agents. Get user profiles, search tweets, access trends, and more.",
  "homepage": "https://scrapebadger.com",
  "repository": "https://github.com/scrape-badger/scrapebadger-mcp",
  "license": "MIT",
  "author": {
    "name": "ScrapeBadger",
    "email": "support@scrapebadger.com",
    "url": "https://scrapebadger.com"
  },
  "categories": [
    "data",
    "social-media",
    "scraping",
    "twitter"
  ],
  "tags": [
    "twitter",
    "x",
    "social-media",
    "scraping",
    "api",
    "tweets",
    "users",
    "trends"
  ],
  "distribution": {
    "type": "pypi",
    "package": "scrapebadger-mcp"
  },
  "runtime": {
    "type": "python",
    "minVersion": "3.10"
  },
  "install": {
    "instructions": "pip install scrapebadger-mcp",
    "command": {
      "command": "uvx",
      "args": ["scrapebadger-mcp"]
    },
    "env": [
      {
        "name": "SCRAPEBADGER_API_KEY",
        "description": "Your ScrapeBadger API key from scrapebadger.com",
        "required": true
      }
    ]
  },
  "capabilities": {
    "tools": true,
    "resources": false,
    "prompts": false
  }
}
```

### Step 4: Publish to Registry

```bash
# Navigate to your repository
cd scrapebadger-mcp

# Publish
mcp publish

# Or with npx
npx @anthropic/mcp-cli publish
```

### Step 5: Verify Publication

Visit [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io) and search for "scrapebadger".

### Troubleshooting

- **"Namespace ownership validation failed"**: Ensure you're logged in with the GitHub account that owns the repository
- **"Package not found"**: Publish to PyPI first (see next section)
- **High traffic errors**: The registry may be busy; retry the publish command

---

## 2. PyPI (Python Package Index)

Publishing to PyPI is required before submitting to the MCP Registry.

### Prerequisites

- PyPI account at [pypi.org](https://pypi.org/account/register/)
- API token at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

### Step 1: Configure PyPI Credentials

Create or edit `~/.pypirc`:

```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

Or use environment variables:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

### Step 2: Build the Package

```bash
cd integrations/scrapebadger-mcp

# Clean previous builds
rm -rf dist/ build/ *.egg-info/

# Build
uv build
# or
python -m build
```

### Step 3: Upload to PyPI

```bash
# Upload to PyPI
uv publish
# or
twine upload dist/*
```

### Step 4: Verify

Visit [pypi.org/project/scrapebadger-mcp/](https://pypi.org/project/scrapebadger-mcp/) to confirm the package is live.

### Test PyPI (Optional)

For testing, use Test PyPI first:

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Install from Test PyPI
pip install --index-url https://test.pypi.org/simple/ scrapebadger-mcp
```

---

## 3. GitHub Repository Setup

A well-configured GitHub repository improves discoverability.

### Step 1: Create Repository

```bash
# Create new repository on GitHub: scrape-badger/scrapebadger-mcp

# Initialize local repo
cd integrations/scrapebadger-mcp
git init
git add .
git commit -m "Initial commit: ScrapeBadger MCP Server"

# Add remote and push
git remote add origin git@github.com:scrape-badger/scrapebadger-mcp.git
git branch -M main
git push -u origin main
```

### Step 2: Configure Repository Settings

1. **About Section**: Add description and topics
   - Description: "MCP server for Twitter/X scraping - enables AI agents to access Twitter data"
   - Topics: `mcp`, `model-context-protocol`, `twitter`, `x`, `scraping`, `ai`, `llm`, `claude`, `chatgpt`

2. **Website**: Add `https://scrapebadger.com`

3. **Enable Issues**: For bug reports and feature requests

4. **Add README badges**: Already included in README.md

### Step 3: Create GitHub Release

```bash
# Tag the release
git tag -a v0.1.0 -m "Initial release"
git push origin v0.1.0
```

Then create a release on GitHub:
1. Go to Releases → Draft a new release
2. Select tag `v0.1.0`
3. Title: "v0.1.0 - Initial Release"
4. Description: Copy from CHANGELOG or describe features
5. Publish release

### Step 4: GitHub Actions (CI/CD)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: uv publish
```

Add `PYPI_API_TOKEN` to repository secrets.

---

## 4. Community Directories

Submit to community-maintained directories for additional visibility.

### Awesome MCP Lists

1. **awesome-mcp-servers**: https://github.com/modelcontextprotocol/awesome-mcp-servers
   - Fork, add entry, submit PR:
   ```markdown
   - [ScrapeBadger](https://github.com/scrape-badger/scrapebadger-mcp) - Twitter/X scraping API for AI agents. Get user profiles, tweets, trends, and more.
   ```

2. **awesome-mcp**: https://github.com/punkpeye/awesome-mcp
   - Similar process: fork, add entry, submit PR

### MCP Server Directories

1. **Smithery.ai**: https://smithery.ai/
   - Submit via their form
   - Provides installation commands for various clients

2. **MCP.so**: https://mcp.so/
   - Community directory of MCP servers
   - Submit via GitHub issue or form

3. **Glama.ai**: https://glama.ai/mcp/servers
   - MCP server discovery platform
   - Submit via their website

### Claude-Specific

1. **Claude Plugins Directory**: If Anthropic launches an official directory
2. **Claube.ai**: https://www.claube.ai/ - Unofficial Claude MCP directory

---

## 5. Marketing & Promotion

### Blog Posts & Announcements

1. **ScrapeBadger Blog**: Write announcement post
   - Title: "Introducing ScrapeBadger MCP: Twitter Data for AI Agents"
   - Cover: Architecture diagram, usage examples

2. **Dev.to**: Publish tutorial
   - Title: "How to Give Claude Access to Twitter Data with ScrapeBadger MCP"

3. **Medium**: Cross-post or unique content

4. **Hashnode**: Technical deep-dive

### Social Media

1. **Twitter/X**: Announce with demo video/GIF
   ```
   Introducing ScrapeBadger MCP - give your AI agents access to Twitter data!

   Claude, ChatGPT, Cursor can now:
   - Get user profiles
   - Search tweets
   - Access trends
   - And more!

   Get started: github.com/scrape-badger/scrapebadger-mcp

   #MCP #AI #LLM #Claude #ChatGPT
   ```

2. **LinkedIn**: Professional announcement

3. **Reddit**:
   - r/ClaudeAI
   - r/ChatGPT
   - r/LocalLLaMA
   - r/MachineLearning

4. **Hacker News**: "Show HN: ScrapeBadger MCP - Twitter API for AI Agents"

### Developer Communities

1. **Discord**:
   - Anthropic Discord (if available)
   - AI/ML Discord servers
   - Developer communities

2. **Slack**:
   - Relevant workspaces

3. **GitHub Discussions**:
   - MCP repository discussions
   - Related project discussions

### Documentation Sites

1. **ScrapeBadger Docs**: Add MCP section
2. **API Reference**: Document MCP tools

---

## Submission Checklist

Use this checklist to track your submissions:

### Required (Do First)

- [ ] **PyPI**: Package published
- [ ] **GitHub**: Repository created with proper settings
- [ ] **MCP Registry**: Server published

### Recommended (Do Second)

- [ ] **GitHub Release**: v0.1.0 created
- [ ] **GitHub Actions**: CI/CD for auto-publishing
- [ ] **awesome-mcp-servers**: PR submitted
- [ ] **Smithery.ai**: Submitted

### Optional (Do Later)

- [ ] **Twitter announcement**: Posted
- [ ] **Blog post**: Published
- [ ] **Reddit/HN**: Shared
- [ ] **Dev.to tutorial**: Published

---

## Maintenance

### Version Updates

When releasing new versions:

1. Update `pyproject.toml` version
2. Update `__init__.py` version
3. Create git tag: `git tag -a v0.2.0 -m "Version 0.2.0"`
4. Push tag: `git push origin v0.2.0`
5. GitHub Release triggers PyPI publish
6. MCP Registry auto-syncs from PyPI (verify manually)

### Monitoring

- Watch GitHub issues for bug reports
- Monitor PyPI download stats
- Check MCP Registry listing periodically
- Respond to community feedback

---

## Resources

- **MCP Registry Docs**: https://github.com/modelcontextprotocol/registry
- **MCP Specification**: https://modelcontextprotocol.io
- **PyPI Publishing Guide**: https://packaging.python.org/tutorials/packaging-projects/
- **GitHub Actions for Python**: https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python

---

## Support

If you encounter issues with registry submission:

- **MCP Registry**: Open issue at https://github.com/modelcontextprotocol/registry/issues
- **PyPI**: Contact PyPI support
- **ScrapeBadger**: support@scrapebadger.com
