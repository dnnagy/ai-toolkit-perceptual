"""Loss-split resolver shared between the trainer and tests.

The trainer alternates the diffusion and depth-consistency losses across
optimizer steps when loss splitting is enabled. The resolver computes the
per-sample mode using the precedence documented in the config schema.
"""
from typing import Union


def resolve_loss_split(
    *,
    ds_value: Union[str, None],
    global_value: Union[str, None],
    global_explicit: bool,
    effective_depth_weight: float,
) -> Union[str, None]:
    """Resolve the loss-split mode for a single sample.

    Returns 'diffusion_depth' (alternation active) or None (split off).

    Precedence:
      1a. ds_value == 'sum'             -> None (per-dataset force off)
      1b. ds_value is not None          -> ds_value (per-dataset force on)
      2.  global_explicit is True       -> global_value (explicit global)
      3.  autodetect                    -> 'diffusion_depth' if
                                            effective_depth_weight > 0
                                            else None
    """
    if ds_value == 'sum':
        return None
    if ds_value is not None:
        return ds_value
    if global_explicit:
        return global_value
    return 'diffusion_depth' if effective_depth_weight > 0.0 else None
