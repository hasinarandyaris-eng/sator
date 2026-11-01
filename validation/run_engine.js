// Extrait la fonction kimber() de index.html et l'exécute sur des cas JSON.
// Usage : node run_engine.js ../index.html cas.json
const fs = require('fs')
const [, , htmlPath, casesPath] = process.argv
const html = fs.readFileSync(htmlPath, 'utf8')
const m = html.match(/function kimber\(rain[\s\S]*?\n\}/)
if (!m) throw new Error('Fonction kimber() introuvable dans ' + htmlPath)
const kimber = new Function(m[0] + '\nreturn kimber')()
const cases = JSON.parse(fs.readFileSync(casesPath, 'utf8'))
const out = cases.map(c => Array.from(kimber(c.rain, c.rate, c.thr, c.grace, c.smax, new Set(c.wash)).loss))
process.stdout.write(JSON.stringify(out))
