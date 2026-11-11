// C07 sample table: tree vs not-tree points with a year of Sentinel-2 features. Run in the Earth Engine Code Editor.
// Adapted from Shajar Ledger gee/c07_benchmark.js (github.com/Baneenraza/Shajar). Same region, year, seeds and
// features, but this script only EXPORTS the samples; the random forest and the threshold baseline are trained
// and scored in Python (verify/c07.py) so the result is reproducible and tested.
// Output: Drive folder "battleverse", file c07_samples.csv -> data/raw/c07_samples.csv
// Columns: label,split,<features>,q1,q2,q3,q4,lon,lat   split = train | test | hand
// Answer key: ESA WorldCover v200 (2021) tree cover = class 10. Water (80) and mangroves (95) excluded.
// The "hand" rows are the same points Shajar's c07/label.html shows (seed 99), for the team's own labels.

var region = ee.Geometry.Rectangle([66.8, 24.0, 69.5, 26.0]); // lower Sindh
var start = ee.Date.fromYMD(2021, 1, 1);

var s2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(region).filterDate(start, start.advance(1, 'year'))
  .map(function (i) {
    var scl = i.select('SCL');
    var clear = scl.neq(3).and(scl.neq(8)).and(scl.neq(9)).and(scl.neq(10)).and(scl.neq(11));
    return i.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12']).divide(10000)
      .addBands(i.normalizedDifference(['B8', 'B4']).rename('ndvi'))
      .addBands(i.normalizedDifference(['B8', 'B11']).rename('ndmi'))
      .updateMask(clear).copyProperties(i, ['system:time_start']);
  });

var ndvi = s2.select('ndvi');
function quarter(q) { return ndvi.filterDate(start.advance(3 * q, 'month'), start.advance(3 * q + 3, 'month')).median().rename('q' + (q + 1)); }
var features = ndvi.reduce(ee.Reducer.percentile([10, 25, 50, 75, 90]))
  .addBands(ndvi.reduce(ee.Reducer.stdDev()))
  .addBands(ndvi.mean().rename('mean'))
  .addBands(s2.select(['B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'ndmi']).median())
  .addBands(quarter(0)).addBands(quarter(1)).addBands(quarter(2)).addBands(quarter(3));

var wc = ee.ImageCollection('ESA/WorldCover/v200').first().select('Map');
var label = wc.eq(10).rename('label').updateMask(wc.neq(80).and(wc.neq(95)));

var COLS = ['ndvi_p10', 'ndvi_p25', 'ndvi_p50', 'ndvi_p75', 'ndvi_p90', 'ndvi_stdDev', 'mean',
  'B2', 'B3', 'B4', 'B8', 'B11', 'B12', 'ndmi', 'q1', 'q2', 'q3', 'q4'];

function balanced(seed, n) {
  var pts = label.sampleRegions({ collection: ee.FeatureCollection.randomPoints(region, 25000, seed), scale: 10, geometries: true });
  var pick = pts.filter(ee.Filter.eq('label', 1)).limit(n).merge(pts.filter(ee.Filter.eq('label', 0)).limit(n));
  return features.sampleRegions({ collection: pick, properties: ['label'], scale: 10, geometries: true, tileScale: 4 })
    .filter(ee.Filter.notNull(COLS))
    .map(function (f) { var c = f.geometry().coordinates(); return f.set({ lon: c.get(0), lat: c.get(1) }); });
}

var data = balanced(7, 1200).randomColumn('r', 11).map(function (f) {
  return f.set('split', ee.Algorithms.If(ee.Number(f.get('r')).lt(0.7), 'train', 'test'));
});
var hand = balanced(99, 100).map(function (f) { return f.set('split', 'hand'); });
var all = data.merge(hand);

print('counts by split', all.aggregate_histogram('split'));
Export.table.toDrive({
  collection: all, description: 'c07_samples', folder: 'battleverse', fileFormat: 'CSV',
  selectors: ['label', 'split'].concat(COLS).concat(['lon', 'lat']),
});
