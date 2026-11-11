"""Every threshold and bound in one place. Values follow the design spec section 8.
Items marked "tune" are starting values to adjust on the first real export."""

RULES = {
    # Gate 1: physical bounds
    "lat_range": (-90.0, 90.0),
    "lon_range": (-180.0, 180.0),
    "site_radius_km": 25.0,            # tune
    "date_min": "2018-07",             # Sentinel-5P OFFL NO2 starts here
    "no2_range": (-0.001, 0.02),       # mol/m2; small negatives are retrieval noise and pass
    "cloud_range": (0.0, 1.0),
    "wind_speed_range": (0.0, 60.0),   # m/s
    "wind_dir_range": (0.0, 360.0),    # degrees
    "calm_wind": 1.0,                  # m/s; below this the plume has no direction
    "irradiance_range": (0.0, 1361.0), # W/m2, solar constant
    "temperature_range": (-40.0, 60.0),
    "fill_values": (-999, -999.0, -9999, -9999.0),  # NASA POWER missing-data markers
    "ndvi_range": (-1.0, 1.0),
    "max_trees_per_acre": 1000,
    # Gate 2: plausibility
    "cf_tolerance": 1.05,              # generation may exceed capacity x hours by 5% before rejection
    # Gate 3: confidence
    "min_overpasses": 5,               # tune
    "ood_margin": 0.10,
    "max_interval_frac": 0.5,          # interval wider than half the max monthly generation -> low confidence
    "max_plot_cloud": 0.30,
    "tree_prob": 0.5,
    "interval_level": 0.80,
    "fy_low_conf_max": 3,              # more low-confidence months than this in a fiscal year -> low confidence
    # C07 pollution baseline: imported-coal fleet utilisation, NEPRA PER Generation FY2024-25 (22.9%)
    "fleet_pf_imported_coal": 0.229,
    # Cross-checks (C12)
    "nepra_match_tol": 0.05,
    "tree_claim_tol": 0.10,
    "internal_match_tol": 0.01,
    # Tree payments (demo values, labelled in the app)
    "price_per_tree_year": 400,        # PKR
    "passes_per_year": 4,
    "farmer_share": 0.6,
    "claim_types": ("generation", "co2_total", "co2_intensity", "reduction_pct", "trees_planted"),
}

# NEPRA plant names that make up each satellite site. Hub's two plants sit ~1 km apart and share one plume.
SITE_PLANTS = {
    "sahiwal": ["Huaneng Shandong Ruyi"],
    "hub": ["China Power Hub Generation", "The Hub Power Company"],
}

BANNED_WORDS = ("fraud", "breach", "proves", "zero carbon", "net zero")
