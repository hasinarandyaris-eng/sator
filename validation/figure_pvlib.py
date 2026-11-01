"""Trace la comparaison SATOR / pvlib sur une année exemple (comparaison_pvlib.png)."""
import json, os, subprocess, sys, tempfile
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pvlib
from pvlib.soiling import kimber

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'index.html')
rng = np.random.default_rng(12)
rain = np.where(rng.random(365) < 0.25, rng.gamma(0.7, 9, 365), 0).round(1)
rain[150:230] = np.where(rain[150:230] > 6, 2.0, rain[150:230])   # été sec
rain[40] = 6.0                                                     # pluie égale au seuil
case = dict(rain=rain.tolist(), rate=0.0015, thr=6, grace=14, smax=0.3, wash=[300])
with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
    json.dump([case], f)
sator = np.array(json.loads(subprocess.check_output(['node', os.path.join(HERE, 'run_engine.js'), HTML, f.name]))[0])
os.unlink(f.name)
idx = pd.date_range('2025-01-01', periods=365)
ref = kimber(pd.Series(rain, idx), cleaning_threshold=6, soiling_loss_rate=0.0015, grace_period=14,
             max_soiling=0.3, manual_wash_dates=idx[[300]], rain_accum_period=24).values

fig, ax = plt.subplots(3, 1, figsize=(12, 8.5), sharex=True, gridspec_kw={'height_ratios': [1, 2.2, 1]})
ax[0].bar(range(365), rain, color='#5B9BD5'); ax[0].axhline(6, ls='--', c='k', lw=1); ax[0].set_ylabel('Pluie (mm)')
ax[0].set_title('SATOR contre pvlib.soiling.kimber : r = 0,15 %/j, seuil 6 mm, grâce 14 j, Smax 30 %, lavage le 28 oct.')
ax[1].plot(ref * 100, c='k', lw=3.5, label=f'pvlib {pvlib.__version__} (référence)')
ax[1].plot(sator * 100, c='#A8205C', lw=1.4, ls='--', label='SATOR')
ax[1].set_ylabel("Perte d'encrassement (%)"); ax[1].legend()
ax[2].plot((sator - ref) * 100, c='#A8205C'); ax[2].axhline(0, c='k', lw=.5)
ax[2].set_ylim(-1e-12, 1e-12); ax[2].set_ylabel('Écart (point de %)'); ax[2].set_xlabel("Jour de l'année")
plt.tight_layout(); plt.savefig(os.path.join(HERE, 'comparaison_pvlib.png'), dpi=110)
print(f"Perte annuelle : pvlib {ref.mean()*100:.3f} %, SATOR {sator.mean()*100:.3f} % | écart max {np.abs(sator-ref).max()*100:.1e} point de %")
