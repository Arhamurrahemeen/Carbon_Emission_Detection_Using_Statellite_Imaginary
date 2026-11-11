// Quarterly Sentinel-2 readings for each tree-offset plot. Run in the Earth Engine Code Editor.
// Adapted from Shajar Ledger gee/export_data.js and gee/c07_benchmark.js (github.com/Baneenraza/Shajar).
// Output: Drive folder "battleverse", file plot_passes.csv -> data/raw/plot_passes.csv
// Columns: plot_id,date,ndvi,cloud,<annual features>
//   ndvi, cloud     clearest Sentinel-2 image within +-15 days of the pass date (Cloud Score+ >= 0.6 = clear)
//   annual features the C07 random forest inputs, over the 12 months before the pass date
// Keep PLOTS in sync with data/manual/plots.csv.

var PLOTS = [
  { id: 'm1', lat: 24.9291, lon: 67.2309, acres: 3 }, { id: 'm2', lat: 25.4796, lon: 69.1744, acres: 3 },
  { id: 's1', lat: 24.97, lon: 67.3, acres: 25 }, { id: 's2', lat: 24.74, lon: 67.6, acres: 32 },
  { id: 's3', lat: 25.38, lon: 68.3, acres: 22 }, { id: 's4', lat: 25.46, lon: 68.72, acres: 2 },
];
var PASS_DATES = ['2025-02-10', '2025-05-12', '2025-08-10', '2025-11-03',
  '2026-02-10', '2026-05-12', '2026-08-10', '2026-11-03'];

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED');
var cloudScore = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var FEATURES = ['ndvi_p10', 'ndvi_p25', 'ndvi_p50', 'ndvi_p75', 'ndvi_p90', 'ndvi_stdDev', 'mean',
  'B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'ndmi'];

function plotGeom(p) { return ee.Geometry.Point([p.lon, p.lat]).buffer(Math.sqrt((p.acres * 4047) / Math.PI)); }

function annualFeatures(geom, end) {
  var col = s2.filterBounds(geom).filterDate(end.advance(-1, 'year'), end).map(function (i) {
    var scl = i.select('SCL');
    var clear = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
    return i.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']).divide(10000)
      .addBands(i.normalizedDifference(['B8', 'B4']).rename('ndvi'))
      .addBands(i.normalizedDifference(['B8', 'B11']).rename('ndmi'))
      .updateMask(clear);
  });
  var ndvi = col.select('ndvi');
  var img = ndvi.reduce(ee.Reducer.percentile([10, 25, 50, 75, 90]))
    .addBands(ndvi.reduce(ee.Reducer.stdDev()))
    .addBands(ndvi.mean().rename('mean'))
    .addBands(col.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'ndmi']).median());
  return img.reduceRegion(ee.Reducer.mean(), geom, 10);
}

function passRow(p, dateStr) {
  var geom = plotGeom(p);
  var d = ee.Date(dateStr);
  var col = s2.filterBounds(geom).filterDate(d.advance(-15, 'day'), d.advance(15, 'day'))
    .linkCollection(cloudScore, ['cs'])
    .map(function (img) {
      var clear = img.select('cs').gte(0.6);
      var cs = clear.reduceRegion(ee.Reducer.mean(), geom, 10).get('cs');
      var cloud = ee.Number(ee.Algorithms.If(cs, ee.Number(1).subtract(cs), 1)); // no clear-sky pixels = fully cloudy
      var ndvi = img.normalizedDifference(['B8', 'B4']).updateMask(clear).reduceRegion(ee.Reducer.mean(), geom, 10).get('nd');
      return img.set({ cloud: cloud, ndvi: ndvi });
    }).sort('cloud');
  var base = ee.Dictionary({ plot_id: p.id, date: dateStr });
  var obs = ee.Dictionary(ee.Algorithms.If(col.size().gt(0),
    ee.Dictionary({ ndvi: col.first().get('ndvi'), cloud: col.first().get('cloud') }), ee.Dictionary({})));
  return ee.Feature(null, base.combine(obs).combine(annualFeatures(geom, d)));
}

var rows = [];
PLOTS.forEach(function (p) { PASS_DATES.forEach(function (dt) { rows.push(passRow(p, dt)); }); });
var fc = ee.FeatureCollection(rows);
print('first rows', fc.limit(5));
Export.table.toDrive({
  collection: fc, description: 'plot_passes', folder: 'battleverse', fileFormat: 'CSV',
  selectors: ['plot_id', 'date', 'ndvi', 'cloud'].concat(FEATURES),
});
