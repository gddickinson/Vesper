// Static-site data layer: answers api('/...') from the JSON files exported by scripts/build_static.py
// (every GET in STATIC_ENDPOINTS of vesper/web/app.py). Everything else runs in the browser.
const files = new Map();

export async function staticApi(path) {
  const rel = path.split('?')[0].replace(/^\/+/, '');
  if (!files.has(rel)) {
    files.set(rel, fetch('api/' + rel + '.json').then(r => {
      if (!r.ok) throw new Error(`${r.status} ${rel}`);
      return r.json();
    }));
  }
  return files.get(rel);
}
