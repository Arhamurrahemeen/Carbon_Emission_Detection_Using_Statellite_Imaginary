// Per-overpass NO2 plume features for each coal plant site. Run in the Earth Engine Code Editor.
// Output: one CSV per site in Google Drive (folder "battleverse"), copy to data/raw/overpasses_<site_id>.csv
// Columns: site_id,date,no2_down,no2_up,no2_raw,wind_u,wind_v,wind_speed,wind_dir,cloud_fraction,n_pixels
//
// Method (design spec 7.1):
//   wind      ERA5-Land hourly 10 m u/v at the hour nearest the overpass, averaged within 15 km of the plant
//             (Hub sits on the coast; ERA5-Land has no sea pixels, so a point sample can be empty)
//   wind_dir  direction the wind blows TOWARDS, degrees from north = atan2(u, v)
//   downwind  NO2 mean in a 7 km circle centred 10 km downwind      (starting values, tune)
//   upwind    NO2 mean in a 7 km circle centred 20 km upwind
//   raw       NO2 mean in a 5 km circle on the plant, no wind used (C07 baseline)
//   km -> degrees: dlat = km / 111.32, dlon = km / (111.32 * cos(lat))
// The OFFL L3 product already drops pixels with qa_value < 0.75. Small negative NO2 is kept (sensor noise).

var SITES = [
  { id: 'sahiwal', lat: 30.7142, lon: 73.2380 },
  { id: 'hub', lat: 24.9147, lon: 66.6888 },  // CPHGC coal + Hub Power RFO, ~1 km apart: one combined plume
];
var START = '2018-07-01';
var END = ee.Date(Date.now());
var NO2 = 'tropospheric_NO2_column_number_density';
var SCALE = 1113;

var s5p = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_NO2');
var era = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY').select(['u_component_of_wind_10m', 'v_component_of_wind_10m']);

function offsetPoint(site, km, bearingDeg) {
  var b = ee.Number(bearingDeg).multiply(Math.PI / 180);
  var dlat = ee.Number(km).multiply(b.cos()).divide(111.32);
  var dlon = ee.Number(km).multiply(b.sin()).divide(111.32 * Math.cos(site.lat * Math.PI / 180));
  return ee.Geometry.Point([dlon.add(site.lon), dlat.add(site.lat)]);
}

function meanIn(img, band, geom) {
  return img.select(band).reduceRegion(ee.Reducer.mean(), geom, SCALE).get(band);
}

function rowsFor(site) {
  var pt = ee.Geometry.Point([site.lon, site.lat]);
  var box = pt.buffer(60000).bounds();
  return s5p.filterBounds(box).filterDate(START, END)
    .filter(ee.Filter.calendarRange(5, 10, 'hour'))  // Pakistan overpass ~06-09 UTC; other orbits have no pixels here
    .map(function (img) {
    var t = img.date();
    var hour = ee.Date(t.millis().divide(3600000).round().multiply(3600000));
    var w = era.filterDate(hour, hour.advance(1, 'hour'));
    // If() only evaluates the branch it takes, so a missing ERA5 hour never touches a null image.
    var uv = ee.Dictionary(ee.Algorithms.If(w.size().gt(0),
      ee.Image(w.first()).rename(['u', 'v']).reduceRegion(ee.Reducer.mean(), pt.buffer(15000), 11132),
      ee.Dictionary({ u: -9999, v: -9999 })));
    var u = ee.Number(uv.get('u'));
    var v = ee.Number(uv.get('v'));
    var speed = u.hypot(v);
    var dir = u.atan2(v).multiply(180 / Math.PI).add(360).mod(360);
    var down = offsetPoint(site, 10, dir).buffer(7000);
    var up = offsetPoint(site, 20, dir.add(180)).buffer(7000);
    var onSite = pt.buffer(5000);
    return ee.Feature(null, {
      site_id: site.id,
      date: t.format('YYYY-MM-dd'),
      no2_down: meanIn(img, NO2, down),
      no2_up: meanIn(img, NO2, up),
      no2_raw: meanIn(img, NO2, onSite),
      wind_u: u,
      wind_v: v,
      wind_speed: speed,
      wind_dir: dir,
      cloud_fraction: meanIn(img, 'cloud_fraction', onSite),
      n_pixels: img.select(NO2).reduceRegion(ee.Reducer.count(), onSite, SCALE).get(NO2),
    });
  }).filter(ee.Filter.notNull(['no2_raw', 'no2_down', 'no2_up']))
    .filter(ee.Filter.gt('wind_u', -9000));
}

SITES.forEach(function (site) {
  var rows = rowsFor(site);
  print(site.id + ': first rows', rows.limit(5));
  Export.table.toDrive({
    collection: rows,
    description: 'overpasses_' + site.id,
    folder: 'battleverse',
    fileFormat: 'CSV',
    selectors: ['site_id', 'date', 'no2_down', 'no2_up', 'no2_raw', 'wind_u', 'wind_v',
      'wind_speed', 'wind_dir', 'cloud_fraction', 'n_pixels'],
  });
});
