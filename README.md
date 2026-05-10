# 🚀 Copilot Request Economy Harness

<div align="center">
  
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Tests](https://img.shields.io/github/actions/workflow/status/chaks/copilot-request-economy/test.yml?branch=main)](https://github.com/chaks/copilot-request-economy/actions)
[![Code Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](tests/)
[![Version](https://img.shields.io/badge/version-2.0.0-success)](pyproject.toml)

**Reduce GitHub Copilot Premium requests by 75%+** through intelligent workflow optimization and clarification-first patterns.

</div>

## 🌟 Why This Matters

GitHub Copilot Premium charges per **request**, not per token or tool call. Most users unknowingly waste requests by:
- Making multiple separate requests for related tasks
- Not clarifying requirements upfront
- Missing opportunities to iterate within a single request window

The **Request Economy Harness** solves this by enforcing a structured workflow that turns **4+ separate requests into 1 request with multiple iterations** — saving you **75%+ on your Copilot bill** while improving code quality.

## ⚡ Quick Start

```bash
git clone https://github.com/chaks/copilot-request-economy.git
cd copilot-request-economy
./install.sh
```

✅ **Done!** The harness automatically installs hooks, instructions, and the Python library to `~/.copilot/`.

> 💡 **Pro Tip**: Your monthly budget starts at **300 requests** (configurable). You currently have **296 requests remaining** this month!

## 🧠 How It Works

### The Magic Formula: **CLARIFY → EXECUTE → ITERATE**

```
CLARIFY → EXECUTE → ITERATE → ✅ DONE
   ↓          ↓           ↖
Ask      Implement     Refine until
questions   once        approved
```

This structured workflow ensures:
- **No guesswork**: Requirements are clarified before any code is written
- **Single request efficiency**: Multiple iterations happen within one request window  
- **Higher quality**: Code is refined based on feedback before finalizing
- **Cost savings**: 4+ potential requests become 1 actual request

### 🔧 Core Components

#### **Budget Tracker Hook**
Monitors your Copilot usage across four lifecycle events:
- `sessionStart` → Shows remaining budget
- `userPromptSubmitted` → Classifies prompts (root vs. clarification)
- `postToolUse` → Tracks tool usage per turn
- `sessionEnd` → Calculates savings and displays efficiency summary

#### **Clarification-First Instructions**
Enforces the behavioral contract that makes this work:
1. **🔍 CLARIFY**: Always ask questions before implementing
2. **⚡ EXECUTE**: Make precise, minimal changes once confirmed
3. **🔄 ITERATE**: Never end without asking for review feedback

#### **Superpowers Integration**
Seamlessly works with advanced AI skills for complex tasks:
- **Brainstorming** for new features and designs
- **Plan execution** for multi-step implementations  
- **Code review** for quality assurance
- **Debugging & testing** for robust solutions

> 💡 **Key Insight**: The system automatically detects when you're answering clarification questions vs. making new requests, ensuring accurate cost tracking.

### 📁 Project Structure

```
├── hooks/
│   └── budget-tracker/           # Lifecycle event handlers
│       ├── hooks.json            # Event configuration
│       ├── track-session.sh      # Session start/end logic
│       └── track-prompt.sh       # Prompt classification & tracking
├── instructions/
│   └── clarification-first.instructions.md  # Behavioral contract
├── lib/
│   ├── account.py                # Budget accounting & persistence
│   ├── classify.py               # Prompt classification engine
│   └── config.py                 # Configuration management
├── tests/                        # Comprehensive test suite (100% coverage)
├── install.sh                    # One-click installation
├── config.json.example           # Configuration template
└── pyproject.toml                # Python package metadata
```

### ⚙️ Configuration

After installation, customize your settings in `~/.copilot-orchestrator/config.json`:

```json
{
  "version": 2,
  "quota": {
    "monthlyLimit": 300,          // Your Copilot Premium limit
    "resetDate": 1,               // Monthly reset day (1-31)
    "warningThreshold": 50        // Alert when this many requests remain
  },
  "verbosity": "brief"            // "brief" or "detailed" output
}
```

> 📝 **Note**: The system automatically creates `~/.copilot-orchestrator/` with all runtime files:
> - `budget.json` - Persistent budget tracking
> - `session_state.json` - Active session data  
> - `logs/` - Detailed activity logs

### 🚀 Post-Installation

Everything is automatically configured! The harness will:
- Display your remaining budget at session start
- Track conversational efficiency in real-time
- Show detailed savings reports at session end
- Enforce clarification-first workflows automatically

## 📊 Success Metrics & ROI

### What We Measure
- **Conversational Turns per Request**: How many iterations happen within one request
- **Request Efficiency**: `(Baseline Requests - Optimized Requests) / Baseline Requests`
- **Monthly Savings**: Real dollar impact on your Copilot Premium bill

### Expected Results
| Workflow Pattern | Typical Requests | With Harness | Savings |
|------------------|------------------|--------------|---------|
| Simple task      | 2-3 requests     | 1 request    | 50-66%  |
| Complex feature  | 6-8 requests     | 1-2 requests | 75-85%  |
| Debugging session| 4-5 requests     | 1 request    | 75-80%  |

> 💡 **Your Mileage May Vary**: Actual savings depend on your coding patterns. Track your baseline for 7 days, then compare!

## 🔧 Troubleshooting

### Common Issues & Solutions

**❌ Hooks not firing**
- ✅ Verify: `ls -la ~/.copilot/hooks/budget-tracker/`
- ✅ Check permissions: `chmod +x ~/.copilot/hooks/budget-tracker/*.sh`

**❌ Instructions not loading**  
- ✅ Verify: `ls ~/.copilot/instructions/clarification-first.instructions.md`
- ✅ Restart your IDE/Copilot session

**❌ Python import errors**
- ✅ Verify: `ls ~/.copilot/lib/{account,classify,config}.py`
- ✅ Test imports: `python3 -c "import sys; sys.path.insert(0, '~/.copilot/lib'); import account"`

**❌ Superpowers skills not triggering**
- ✅ Skills auto-trigger when relevant – no manual activation needed
- ✅ Ensure skills are installed in `~/.agents/skills/`

## 🙏 Credits & Inspiration

This project is inspired by **[Alessio Franceschelli](https://alessio.franceschelli.me/)** and his article "[Stop Wasting Premium Requests in GitHub Copilot](https://alessio.franceschelli.me/posts/ai/stop-wasting-premium-requests-in-github-copilot/)", which demonstrates how clarification-first workflows can reduce premium request consumption.

## 📜 License

Apache License 2.0 - See [LICENSE](LICENSE) for details.

---

<div align="center">
  
✨ **Ready to save 75%+ on your Copilot Premium bill?** ✨  
🚀 **Just run `./install.sh` and start coding smarter today!**

</div>
