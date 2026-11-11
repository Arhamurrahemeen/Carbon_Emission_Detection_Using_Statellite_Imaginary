# Earth Engine exports

Run each script in the [Earth Engine Code Editor](https://code.earthengine.google.com), signed in with the team account (project `shajar-514406`). Python never calls Earth Engine; it only reads the CSVs below.

1. **`overpass_export.js`**: paste, click **Run**, then **Tasks → Run** on `overpasses_sahiwal` and `overpasses_hub`. Each takes several minutes (about 2,000+ satellite passes per site since July 2018). Download from Drive folder `battleverse` to `data/raw/overpasses_sahiwal.csv` and `data/raw/overpasses_hub.csv`.
2. **`plots_export.js`**: paste, Run, then Tasks → Run `plot_passes`. Save to `data/raw/plot_passes.csv`. Keep the `PLOTS` list in sync with `data/manual/plots.csv`.
3. **`c07_tree_samples.js`**: paste, Run, then Tasks → Run `c07_samples`. Save to `data/raw/c07_samples.csv`.
4. **Hand labels (C07):** in Shajar's `c07/label.html`, after labelling, open the browser console and run `copy(localStorage.getItem('shajar_c07_labels'))`, paste into a file, and convert it to `data/raw/c07_hand_labels.csv` with columns `lon,lat,label` (1 = tree, 0 = not tree).

Then rebuild: `python -m verify.build`.

Check before trusting a run: the `print` output shows the first rows. `no2_*` values should be around 1e-5 to 1e-4 mol/m², and `wind_speed` between 0 and ~15 m/s.
