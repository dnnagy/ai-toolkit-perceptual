#!/usr/bin/env python3
"""Tests for loss-split resolution and config validation.

Covers:
  - resolve_loss_split() resolver: per-dataset / global / autodetect precedence
  - DatasetConfig.loss_split validation: None / 'diffusion_depth' / 'sum'
  - TrainConfig.loss_split validation + _loss_split_explicit tracking

Run: python testing/test_loss_split.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from toolkit.loss_split import resolve_loss_split


# ============================================================
# resolve_loss_split — per-dataset wins
# ============================================================

def test_per_dataset_force_on_overrides_global_off():
    """Per-dataset 'diffusion_depth' wins even when global is explicit None."""
    out = resolve_loss_split(
        ds_value='diffusion_depth',
        global_value=None,
        global_explicit=True,
        effective_depth_weight=0.0,
    )
    assert out == 'diffusion_depth', f"expected 'diffusion_depth', got {out!r}"
    print("  PASS test_per_dataset_force_on_overrides_global_off")


def test_per_dataset_force_off_overrides_global_on():
    """Per-dataset 'sum' wins even when global is force-on."""
    out = resolve_loss_split(
        ds_value='sum',
        global_value='diffusion_depth',
        global_explicit=True,
        effective_depth_weight=1.0,
    )
    assert out is None, f"expected None, got {out!r}"
    print("  PASS test_per_dataset_force_off_overrides_global_on")


def test_per_dataset_force_off_overrides_autodetect():
    """Per-dataset 'sum' wins over autodetect (depth weight > 0)."""
    out = resolve_loss_split(
        ds_value='sum',
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.5,
    )
    assert out is None, f"expected None, got {out!r}"
    print("  PASS test_per_dataset_force_off_overrides_autodetect")


def test_per_dataset_force_on_overrides_autodetect_off():
    """Per-dataset 'diffusion_depth' wins over autodetect off."""
    out = resolve_loss_split(
        ds_value='diffusion_depth',
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.0,
    )
    assert out == 'diffusion_depth', f"expected 'diffusion_depth', got {out!r}"
    print("  PASS test_per_dataset_force_on_overrides_autodetect_off")


# ============================================================
# resolve_loss_split — explicit global (per-dataset unset)
# ============================================================

def test_global_force_on_with_per_dataset_unset():
    """Global 'diffusion_depth' applies when per-dataset is None."""
    out = resolve_loss_split(
        ds_value=None,
        global_value='diffusion_depth',
        global_explicit=True,
        effective_depth_weight=0.0,
    )
    assert out == 'diffusion_depth', f"expected 'diffusion_depth', got {out!r}"
    print("  PASS test_global_force_on_with_per_dataset_unset")


def test_global_force_off_with_per_dataset_unset():
    """Global explicit None applies (force off) when per-dataset is None."""
    out = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=True,
        effective_depth_weight=1.0,  # depth active but global says off
    )
    assert out is None, f"expected None, got {out!r}"
    print("  PASS test_global_force_off_with_per_dataset_unset")


# ============================================================
# resolve_loss_split — autodetect (per-dataset unset, global not explicit)
# ============================================================

def test_autodetect_on_when_depth_active():
    """Autodetect enables 'diffusion_depth' when effective depth weight > 0."""
    out = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.005,
    )
    assert out == 'diffusion_depth', f"expected 'diffusion_depth', got {out!r}"
    print("  PASS test_autodetect_on_when_depth_active")


def test_autodetect_off_when_depth_inactive():
    """Autodetect disables when effective depth weight is 0."""
    out = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.0,
    )
    assert out is None, f"expected None, got {out!r}"
    print("  PASS test_autodetect_off_when_depth_inactive")


def test_autodetect_boundary_zero_is_off():
    """Autodetect: weight exactly 0 is off (strict > 0 check)."""
    out = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.0,
    )
    assert out is None
    # Tiny positive weight should turn it on.
    out2 = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=False,
        effective_depth_weight=1e-9,
    )
    assert out2 == 'diffusion_depth', f"expected 'diffusion_depth', got {out2!r}"
    print("  PASS test_autodetect_boundary_zero_is_off")


# ============================================================
# Schema validation
# ============================================================

def test_dataset_config_loss_split_accepts_valid_values():
    """DatasetConfig accepts None, 'diffusion_depth', 'sum'."""
    from toolkit.config_modules import DatasetConfig
    for v in (None, 'diffusion_depth', 'sum'):
        d = DatasetConfig(folder_path='/tmp/test', loss_split=v)
        assert d.loss_split == v, f"expected loss_split={v!r}, got {d.loss_split!r}"
    print("  PASS test_dataset_config_loss_split_accepts_valid_values")


def test_dataset_config_loss_split_default_is_none():
    """DatasetConfig.loss_split defaults to None (inherit from global)."""
    from toolkit.config_modules import DatasetConfig
    d = DatasetConfig(folder_path='/tmp/test')
    assert d.loss_split is None
    print("  PASS test_dataset_config_loss_split_default_is_none")


def test_dataset_config_loss_split_rejects_unknown():
    """DatasetConfig raises on unknown loss_split values."""
    from toolkit.config_modules import DatasetConfig
    for bad in ('off', 'on', 'true', 'diffusion', '', 'sum_diffusion'):
        try:
            DatasetConfig(folder_path='/tmp/test', loss_split=bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for loss_split={bad!r}")
    print("  PASS test_dataset_config_loss_split_rejects_unknown")


def test_train_config_loss_split_explicit_tracking():
    """TrainConfig._loss_split_explicit reflects whether the key was passed."""
    from toolkit.config_modules import TrainConfig

    # Key absent -> not explicit, value None
    t1 = TrainConfig()
    assert t1._loss_split_explicit is False, "expected _loss_split_explicit=False when absent"
    assert t1.loss_split is None

    # Key explicit None -> explicit, value None
    t2 = TrainConfig(loss_split=None)
    assert t2._loss_split_explicit is True, "expected _loss_split_explicit=True for explicit None"
    assert t2.loss_split is None

    # Key explicit 'diffusion_depth' -> explicit, value 'diffusion_depth'
    t3 = TrainConfig(loss_split='diffusion_depth')
    assert t3._loss_split_explicit is True
    assert t3.loss_split == 'diffusion_depth'
    print("  PASS test_train_config_loss_split_explicit_tracking")


def test_train_config_loss_split_rejects_unknown():
    """TrainConfig raises on unknown loss_split values."""
    from toolkit.config_modules import TrainConfig
    for bad in ('off', 'sum', 'true', 'diffusion'):
        try:
            TrainConfig(loss_split=bad)
        except ValueError:
            continue
        raise AssertionError(f"expected ValueError for loss_split={bad!r}")
    print("  PASS test_train_config_loss_split_rejects_unknown")


# ============================================================
# Integration-style: combinations the user is likely to write
# ============================================================

def test_user_scenario_default_config_with_depth():
    """Typical config: depth_consistency.loss_weight: 0.005, no train.loss_split.
    Expected: every sample auto-enables 'diffusion_depth'."""
    out = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.005,
    )
    assert out == 'diffusion_depth'
    print("  PASS test_user_scenario_default_config_with_depth")


def test_user_scenario_legacy_config_with_explicit_per_dataset():
    """Backward-compat: existing configs with per-dataset 'diffusion_depth' still work."""
    out = resolve_loss_split(
        ds_value='diffusion_depth',
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.005,
    )
    assert out == 'diffusion_depth'
    print("  PASS test_user_scenario_legacy_config_with_explicit_per_dataset")


def test_user_scenario_no_depth_no_split():
    """No depth anchor, no global override -> autodetect off."""
    out = resolve_loss_split(
        ds_value=None,
        global_value=None,
        global_explicit=False,
        effective_depth_weight=0.0,
    )
    assert out is None
    print("  PASS test_user_scenario_no_depth_no_split")


def test_user_scenario_global_on_with_one_dataset_opted_out():
    """Global force-on, but one dataset opts out via 'sum'. Verifies the
    cross-dataset use case the global setting was added for."""
    out_default = resolve_loss_split(
        ds_value=None,
        global_value='diffusion_depth',
        global_explicit=True,
        effective_depth_weight=0.005,
    )
    assert out_default == 'diffusion_depth', "default dataset should split"

    out_opted_out = resolve_loss_split(
        ds_value='sum',
        global_value='diffusion_depth',
        global_explicit=True,
        effective_depth_weight=0.005,
    )
    assert out_opted_out is None, "'sum' dataset should not split"
    print("  PASS test_user_scenario_global_on_with_one_dataset_opted_out")


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("\n=== Per-dataset wins ===")
    test_per_dataset_force_on_overrides_global_off()
    test_per_dataset_force_off_overrides_global_on()
    test_per_dataset_force_off_overrides_autodetect()
    test_per_dataset_force_on_overrides_autodetect_off()

    print("\n=== Explicit global ===")
    test_global_force_on_with_per_dataset_unset()
    test_global_force_off_with_per_dataset_unset()

    print("\n=== Autodetect ===")
    test_autodetect_on_when_depth_active()
    test_autodetect_off_when_depth_inactive()
    test_autodetect_boundary_zero_is_off()

    print("\n=== Schema validation ===")
    test_dataset_config_loss_split_accepts_valid_values()
    test_dataset_config_loss_split_default_is_none()
    test_dataset_config_loss_split_rejects_unknown()
    test_train_config_loss_split_explicit_tracking()
    test_train_config_loss_split_rejects_unknown()

    print("\n=== User scenarios ===")
    test_user_scenario_default_config_with_depth()
    test_user_scenario_legacy_config_with_explicit_per_dataset()
    test_user_scenario_no_depth_no_split()
    test_user_scenario_global_on_with_one_dataset_opted_out()

    print("\n=== ALL 17 TESTS PASSED ===")
