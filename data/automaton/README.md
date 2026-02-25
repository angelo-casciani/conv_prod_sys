# Automaton Directory

This directory contains Stochastic Knowledge Graphs (SKGs) in UPPAAL XML format, which represent learned process behaviors from event logs.

## Structure

```
automaton/
├── default/              # Reference/fallback SKG files
│   └── *.xml            # Default SKG used when extraction fails
└── *_skg.xml            # Learned SKG files (auto-generated, git-ignored)
```

## SKG Extraction

SKGs are automatically extracted during the parameter extraction pipeline using the [LSHA tool](https://github.com/LesLivia/lsha/tree/xes_extension).

### How It Works

1. When `Extractor.extract_model()` processes an XES event log:
   - DTLogExtSim extracts simulation parameters → saved to `data/parameters/`
   - LSHA extracts the SKG automaton → saved to `data/automaton/`

2. The SKG learning uses a configurable time window (default: 5 minutes) to analyze event sequences and their temporal relationships.

3. If SKG extraction fails (e.g., LSHA not installed, insufficient data), the system automatically falls back to the default SKG in the `default/` subdirectory.

### Generated Files

Learned SKG files follow the naming pattern: `{log_filename}_skg.xml`

**Example:**
- Input: `log/event_log_250905.xes`
- Output: `automaton/event_log_250905_skg.xml`

## Version Control

- ✅ **Committed to Git:** `default/*.xml` (reference files)
- ❌ **Git-ignored:** `*.xml` at root level (auto-generated files)

This approach keeps the repository clean while preserving reference models and allowing local SKG generation.

## LSHA Integration

The LSHA tool is integrated as a Git submodule in `src/lsha/` (branch: `xes_extension`).

### Setup Instructions

If you're cloning this repository for the first time:

```bash
# Clone with submodules
git clone --recurse-submodules <repository-url>

# Or if already cloned, initialize submodules
git submodule update --init --recursive
```

### Installing LSHA Dependencies

```bash
# Activate your virtual environment first
source .venv/bin/activate

# Install dependencies (included in main requirements.txt)
pip install -r requirements.txt

# Or install LSHA requirements separately
pip install -r src/lsha/requirements.txt
```

## Manual SKG Extraction

You can also run the automaton learner standalone:

```bash
cd src
python automaton_learning.py /path/to/event_log.xes --output my_skg.xml --window 5
```

**Parameters:**
- `--output, -o`: Output filename (default: `learned_skg.xml`)
- `--window, -w`: Learning time window in minutes (default: 5)

## Troubleshooting

### LSHA Not Found

If you see: `Warning: LSHA not found. SKG extraction will be skipped.`

**Solution:** Ensure the LSHA submodule is initialized:
```bash
git submodule update --init src/lsha
```

### Import Errors

If LSHA modules fail to import:

**Solution:** Install dependencies:
```bash
pip install -r src/lsha/requirements.txt
```

### Extraction Fails

If SKG extraction fails, the system will:
1. Log the error
2. Automatically copy the default SKG from `default/`
3. Continue with the pipeline using the fallback model

Check logs for specific error messages to diagnose the issue.

## Related Documentation

- [LSHA Original Repository](https://github.com/LesLivia/lsha)
- [LSHA XES Extension Branch](https://github.com/LesLivia/lsha/tree/xes_extension)
- Project simulation parameters: `data/parameters/`
