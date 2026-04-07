#!/usr/bin/env python3
"""Test runner — discovers and runs all tests without pytest."""

import sys
import traceback

# collect all test functions
test_modules = [
    "tests.test_genome",
    "tests.test_organism",
    "tests.test_spatial",
    "tests.test_world",
    "tests.test_terrain",
    "tests.test_species",
    "tests.test_pheromones",
    "tests.test_memory",
    "tests.test_daynight",
    "tests.test_sharing",
    "tests.test_herding",
    "tests.test_pack_hunting",
    "tests.test_territory",
    "tests.test_phylogeny",
    "tests.test_presets",
    "tests.test_death_cause",
    "tests.test_symbiosis",
    "tests.test_behavior",
    "tests.test_food_chain",
    "tests.test_genealogy",
    "tests.test_carrying_capacity",
    "tests.test_genome_export",
    "tests.test_env_zones",
    "tests.test_genetics",
    "tests.test_adaptation",
    "tests.test_kill_heatmap",
    "tests.test_scars",
    "tests.test_fatigue",
    "tests.test_stamina",
]

passed = 0
failed = 0
errors = []

for mod_name in test_modules:
    try:
        mod = __import__(mod_name, fromlist=[""])
    except Exception as e:
        print(f"  ERROR importing {mod_name}: {e}")
        failed += 1
        errors.append((mod_name, str(e)))
        continue

    test_funcs = [name for name in dir(mod) if name.startswith("test_")]
    for func_name in sorted(test_funcs):
        full_name = f"{mod_name}::{func_name}"
        try:
            func = getattr(mod, func_name)
            func()
            print(f"  PASS  {full_name}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {full_name}: {e}")
            failed += 1
            errors.append((full_name, str(e)))
        except Exception as e:
            print(f"  ERROR {full_name}: {e}")
            traceback.print_exc()
            failed += 1
            errors.append((full_name, str(e)))

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")

if errors:
    print("\nFailures:")
    for name, err in errors:
        print(f"  {name}: {err}")

sys.exit(0 if failed == 0 else 1)
