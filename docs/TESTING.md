# Scriber Automated Test Suite & Verification Guide

Scriber features a test battery covering hardware probing, model cache validation, speech transcription, acoustic diarization, voice profiling, REST API contracts, and user interface consistency.

---

## 1. Quickstart: Running Tests

```powershell
# Activate local environment
.venv\Scripts\activate

# Run the complete test suite
python -m unittest discover tests -p "test_*.py"

# Run diverse diarization cases (monologues, dialogues, close-pitch)
python -m unittest tests/test_diverse_cases.py

# Run server API contract tests
python -m unittest tests/test_server_api.py

# Run GPU hardware detection and local cache tests
python -m unittest tests/test_gpu_cache_local.py
```

---

## 2. End-to-End (E2E) Test Suite

The repository includes a 4-tier E2E testing framework in `tests/e2e_suite/`:

```
tests/e2e_suite/
├── helpers.py               # Deterministic audio synthesis and PCM16 containers
├── runner.py                # Unified CLI runner with tier filtering
├── test_tier1_features.py   # Tier 1: Isolated Feature Verification (F1 to F20)
├── test_tier2_boundaries.py # Tier 2: Boundary & Corner Cases
├── test_tier3_pairwise.py   # Tier 3: Cross-Subsystem Interactions
└── test_tier4_scenarios.py  # Tier 4: Real-World Studio Workflows
```

### Running via E2E Runner CLI

```powershell
# Run all 4 tiers
python tests/e2e_suite/runner.py --all

# Run specific tiers
python tests/e2e_suite/runner.py --tier 1
python tests/e2e_suite/runner.py --tier 2
python tests/e2e_suite/runner.py --tier 3
python tests/e2e_suite/runner.py --tier 4
```

---

## 3. Key Test Targets & Benchmarks

- **Single-Speaker Monologue Cohesion**: Verifies that 1-person recordings (e.g. speeches, presentations) are not fragmented across artificial speaker IDs.
- **Same-Gender Dialogue Segregation**: Validates that 2 speakers of the same gender and similar pitch (e.g. Jenny and Emma) are properly segregated into distinct speaker labels.
- **High-Throughput Scaling**: Ensures 90-minute media with 3,000+ segments process without clustering bottlenecks.
- **Zero Cloud API Exposure**: Validates that setting cloud API keys does not trigger external requests and that local execution remains strictly offline.
