import pylab
import numpy as np
from StringIO import StringIO
import os, csv

from matplotlib.mlab import csv2rec, rec2csv

from nipy.fixes.scipy.stats.models.regression import OLSModel, ARModel
from nipy.modalities.fmri.fmristat import hrf as delay
from nipy.modalities.fmri import formula, design, hrf
from nipy.io.api import load_image, save_image
from nipy.core import api

event = [(0,3),(0,4)] # Sequences with all the (subj, run) event designs 
block = [(0,1),(0,2)] # Sequences with all the (subj, run) block designs 

def rewrite_spec(specfile):
    """
    Take a FIAC specification file and get two specifications
    (experiment, begin)
    """
    if 'bloc' in specfile:
        designtype = 'bloc'
    else:
        designtype = 'evt'

    eventdict = {1:'SSt_SSp', 2:'SSt_DSp', 3:'DSt_SSp', 4:'DSt_DSp'}
    s = StringIO()
    w = csv.writer(s)
    w.writerow(['time', 'sentence', 'speaker'])

    d = np.loadtxt(specfile)
    for row in d:
        w.writerow([row[0]] + eventdict[row[1]].split('_'))
    s.seek(0)
    d = csv2rec(s)

    # Now, take care of the 'begin' event
    # This is due to the FIAC design
    if designtype == 'evt':
        b = np.array([(d[0]['time'], 'initial')], np.dtype([('time', np.float),
                                                            ('initial', 'S7')]))
        d = d[1:]
    else:
        k = np.equal(np.arange(d.shape[0]) % 6, 0)
        b = np.array([(tt, 'initial') for tt in d[k]['time']], np.dtype([('time', np.float),
                                                                         ('initial', 'S7')]))
        d = d[~k]

    return d, b

root = "/home/jtaylo/FIAC-HBM2009"

def runscript():

    tv = np.arange(191)*2.5+1.25
    t = formula.make_recarray(tv, 't')

    for subj, r in block + event:
        if (subj, r) in event:
            designtype = 'evt'
        else:
            designtype = 'bloc'

        # Fix the format of the specification so it is
        # more in the form of a 2-way ANOVA

        experiment, initial = rewrite_spec("%(root)s/fiac%(subj)d/subj%(subj)d_%(design)s_fonc%(run)d.txt" % {'root':root, 'subj':subj, 'run':r, 'design':designtype})

        fname = "%(root)s/fiac%(subj)d/subj%(subj)d_%(design)s_fonc%(run)d_experiment.csv" % {'root':root, 'subj':subj, 'run':r, 'design':designtype}
        rec2csv(experiment, fname)
        experiment = csv2rec(fname)

        fname = "%(root)s/fiac%(subj)d/subj%(subj)d_%(design)s_fonc%(run)d_initial.csv" % {'root':root, 'subj':subj, 'run':r, 'design':designtype}
        rec2csv(initial, fname)
        initial = csv2rec(fname)

        X_exper, cons_exper = design.event_design(experiment, t, hrfs=delay.spectral)

        # Ignore the contrasts for 'initial' event type
        # as they are "uninteresting"

        X_initial, _ = design.event_design(initial, t, hrfs=[hrf.glover]) 

        stop 
    #    pylab.clf(); pylab.plot(X_begin); pylab.show()

        # drift

        drift = np.array([tv**i for i in range(4)] + [(tv-tv.mean())**3 * (np.greater(tv, tv.mean()))])
        for i in range(drift.shape[0]):
            drift[i] /= drift[i].max()
        drift = drift.T
        X, cons = design.stack_designs((X_exper, cons_exper),
                                       (X_begin, {}),
                                       (drift, {}))
        tcons = {}
        fcons = {}
        for k, v in cons.items():
            if v.ndim > 1:
                fcons[k] = v
            else:
                tcons[k] = v
        del(cons)

        print tcons, fcons
        m = OLSModel(X)
        f = np.array(load_image("%(root)s/fiac%(subj)d/fonc%(run)d/fsl/filtered_func_data.img" % {'root':root, 'subj':subj, 'run':r}))
        f = np.transpose(f, [3,2,1,0])
        mm = load_image("%(root)s/fiac%(subj)d/fonc%(run)d/fsl/mask.img" % {'root':root, 'subj':subj, 'run':r})
        mma = np.transpose(np.array(mm), [2,1,0])
        ar = np.zeros(f.shape[1:])

        for s in range(f.shape[1]):
            print s
            d = np.array(f[:,s])
            flatd = d.reshape((d.shape[0], np.product(d.shape[1:])))
            result = m.fit(flatd)
            ar[s] = ((result.resid[1:] * result.resid[:-1]).sum(0) / (result.resid**2).sum(0)).reshape(ar.shape[1:])

        # round AR to nearest one-hundredth

        ar *= 100
        ar = ar.astype(np.int) / 100.
        # smooth here?
        # ar = smooth(ar, 8.0)

        output = {}
        for n in tcons.keys():
            output[n] = {}
            output[n]['sd'] = np.zeros(f.shape[1:])
            output[n]['t'] = np.zeros(f.shape[1:])
            output[n]['effect'] = np.zeros(f.shape[1:])

        for n in fcons.keys():
            output[n] = np.zeros(f.shape[1:])

        arvals = np.unique(ar)
        for val in arvals:
            mask = np.equal(ar, val)
            mask *= mma
            m = ARModel(X, val)
            d = f[:,mask]
            results = m.fit(d)
            print val, mask.sum()

            for n in tcons.keys():
                o = output[n]
                resT = results.Tcontrast(tcons[n])
                output[n]['sd'][mask] = resT.sd
                output[n]['t'][mask] = resT.t
                output[n]['effect'][mask] = resT.effect
            # Where should we save these? 

            for n in fcons.keys():
                output[n][mask] = results.Fcontrast(fcons[n]).F

        odir = "script_test/subject%d/run%d" % (subj, r)
        os.system('mkdir -p %s' % odir)
        for n in fcons.keys():
            im = api.Image(output[n], mm.coordmap.copy())
            os.system('mkdir -p %s/%s' % (odir, n))
            # this fails for me, with an error from my version of nifticlib
            save(im, "%s/%s/F.nii" % (odir, n))
            np.save('%s/%s/F' % (odir, n), output[n])

        for n in tcons.keys():
            im = api.Image(output[n], mm.coordmap.copy())
            os.system('mkdir -p %s/%s' % (odir, n))
            # this fails for me, with an error from my version of nifticlib
            # save(im, "%s/%s/F.nii" % (odir, n))
            save_image('%s/%s/t.nii' % (odir, n), output[n]['t'])
            save_image('%s/%s/sd.nii' % (odir, n), output[n]['sd'])
            save_image('%s/%s/effect.nii' % (odir, n), output[n]['effect'])
