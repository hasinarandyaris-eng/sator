"""
Validation de SATOR contre pvlib.soiling.kimber.

Le script donne exactement la même pluie et les mêmes paramètres :
  1) à la fonction officielle pvlib.soiling.kimber (Python) ;
  2) au moteur de SATOR, extrait tel quel de index.html et exécuté avec Node.js.
Il compare ensuite les pertes jour par jour.

Usage :  python compare_pvlib.py            (teste ../index.html)
         python compare_pvlib.py chemin/vers/index.html
Prérequis : Python 3.9+, Node.js 18+, pip install -r requirements.txt
"""
import json, os, subprocess, sys, tempfile
import numpy as np
import pandas as pd
import pvlib
from pvlib.soiling import kimber

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'index.html')
N_CASES = 400

rng = np.random.default_rng(2026)
idx = pd.date_range('2025-01-01', periods=365, freq='D')
cases = []
for k in range(N_CASES):
    p_rain = rng.uniform(0.05, 0.6)
    rain = np.where(rng.random(365) < p_rain, rng.gamma(0.7, rng.uniform(3, 12), 365), 0).round(1)
    thr = int(rng.integers(1, 16))
    if k % 5 == 0:                      # pluies exactement égales au seuil (le seuil est strict)
        rain[rng.integers(0, 365, 10)] = thr
    if k % 7 == 0:                      # forte pluie le 1er janvier
        rain[0] = 40.0
    if k % 11 == 0:                     # longue sécheresse pour atteindre le plafond Smax
        rain[100:300] = 0
    wash = sorted(set(int(x) for x in rng.integers(0, 365, int(rng.integers(0, 13)))))
    cases.append(dict(rain=rain.tolist(),
                      rate=int(rng.integers(1, 31)) / 10000,   # 0,01 à 0,30 %/jour
                      thr=thr,                                 # 1 à 15 mm
                      grace=int(rng.integers(0, 31)),          # 0 à 30 jours
                      smax=int(rng.integers(2, 51)) / 100,     # 2 à 50 %
                      wash=wash))                              # 0 à 12 lavages

with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
    json.dump(cases, f)
engine = os.path.join(HERE, 'run_engine.js')
sator = json.loads(subprocess.check_output(['node', engine, HTML, f.name]))
os.unlink(f.name)

worst_day = worst_year = 0.0
failures = 0
for c, s in zip(cases, sator):
    ref = kimber(pd.Series(c['rain'], idx), cleaning_threshold=c['thr'],
                 soiling_loss_rate=c['rate'], grace_period=c['grace'],
                 max_soiling=c['smax'],
                 manual_wash_dates=idx[c['wash']] if c['wash'] else None,
                 rain_accum_period=24).values
    s = np.array(s)
    gap = np.abs(ref - s).max()
    worst_day = max(worst_day, gap)
    worst_year = max(worst_year, abs(ref.mean() - s.mean()))
    failures += gap > 1e-9

print(f"pvlib {pvlib.__version__} | {N_CASES} années testées ({N_CASES * 365} jours)")
print(f"Cas différents de pvlib : {failures} sur {N_CASES}")
print(f"Écart journalier maximal : {worst_day * 100:.1e} point de %")
print(f"Écart maximal sur la perte annuelle : {worst_year * 100:.1e} point de %")
print("RÉSULTAT :", "identique à pvlib" if failures == 0 else "ÉCARTS DÉTECTÉS")
sys.exit(1 if failures else 0)
