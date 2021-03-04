#!/bin/env python
# how to make mc request soon your grid pack are ready :https://indico.cern.ch/event/321290/contributions/744568/attachments/620452/853749/McM_Tutorial_OPT.pdf
#                                                       https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideSubgroupMC
import os
import math
import json
import shutil
import stat
import argparse

import logging
LOG_LEVEL = logging.DEBUG
logging.root.setLevel(LOG_LEVEL)
stream = logging.StreamHandler()
stream.setLevel(LOG_LEVEL)
logger = logging.getLogger("ZA GridPack-PRODUCTION")
logger.setLevel(LOG_LEVEL)
logger.addHandler(stream)
try:
    from colorlog import ColoredFormatter
    LOGFORMAT = "  %(log_color)s%(levelname)-8s%(reset)s | %(log_color)s%(message)s%(reset)s"
    formatter = ColoredFormatter(LOGFORMAT)
    stream.setFormatter(formatter)
except ImportError:
    pass

if "CMSSW_BASE" not in os.environ:
    raise RuntimeError("This script needs to be run in a CMSSW environment, with cp3_llbb/Calculators42HDM set up")
CMSSW_Calculators42HDM = os.path.join(os.environ["CMSSW_BASE"], "src", "cp3_llbb", "Calculators42HDM")

from cp3_llbb.Calculators42HDM.Calc2HDM import Calc2HDM

def makeGridPoints(dataDir="./data"):
    grid = {}
    grid['example_card'] = [
        ( 500, 300),
        ]
    grid['fullsim'] = [
        #(MH, MA)
        ( 500, 300),
        ( 200, 50), ( 200, 100),
        ( 250, 50), ( 250, 100),
        ( 300, 50), ( 300, 100), ( 300, 200),
        ( 500, 50), ( 500, 100), ( 500, 200), ( 500, 300), ( 500, 400),
        ( 650, 50),
        ( 800, 50), ( 800, 100), ( 800, 200),              ( 800, 400),              ( 800, 700),
        (1000, 50),              (1000, 200),                           (1000, 500),
    ]
    
    with open(os.path.join(dataDir, 'points_1.000000_1.000000.json')) as f:
        d = json.load(f)
        # format the output into tuples
        grid['ellipses_rho_1'] = [(mH, mA,) for mA, mH in d]
    
    with open(os.path.join(dataDir, 'points_0.500000_0.500000.json')) as f:
        d = json.load(f)
        # format the output into tuples
        grid['ellipses_rho_0p5'] = [(mH, mA,) for mA, mH in d]
    return grid

def mass_to_string(m):
    r = '{:.2f}'.format(m)
    r = r.replace('.', 'p')
    return r

def float_to_mass(m):
    r = '{:.2f}'.format(m)
    return float(r)

def getLHAPDF(lhaid=None, lhapdfsets="DEFAULT", scheme=None):
    ## returns pdfname (to pass to setpdf) and lhaid for run card
    if lhapdfsets == 'DEFAULT':
        logger.warning( 'The following ** $DEFAULT_PDF_SETS ** is shortcuts to have the PDF sets automatically added to the run_card at run time to avoid specifying them directly\n. Be careful this is valid at both LO and NLO !\n')
        return lhapdfsets, '$DEFAULT_PDF_SETS'
    elif lhapdfsets == 'NNPDF31':
        if scheme == '4FS':
            logger.info( '''No PDFSETS is given !**  LHA PDF set = NNPDF31  # Positive definite 4Flavor-scheme set will be used instead\n
                            LHA Name = NNPDF31_nnlo_as_0118_nf_4_mc_hessian\n
                            LHA ID = 325500\n
                            make sure this is compatible with the generated process in the proc_card and lhaid in the run_card **\n'''
                )
            return 'NNPDF31_nnlo_as_0118_nf_4_mc_hessian', 325500
        else:
            logger.info( '''No PDFSETS is given !**  LHA PDF set = NNPDF31  # Positive definite set will be used instead\n
                            LHA Name = NNPDF31_nnlo_as_0118_mc_hessian_pdfas\n
                            LHA ID = 325300\n
                            make sure this is compatible with the generated process in the proc_card and lhaid in the run_card **\n'''
                )
            return 'NNPDF31_nnlo_as_0118_mc_hessian_pdfas', 325300
    else:
        if lhaid is None:
            logger.error( "CRITICAL: lhaid can't be NONE ")
        return lhapdfsets, lhaid

def compute_widths_BR_and_lambdas(mH, mA, mh, tb, pdfName="DEFAULT"):
    mode = 'H'
    if mA > mH:
        logger.info("MA_{} > MH_{} switching to A->ZH mode!".format(mA, mH))
        mode = 'A'
    elif mH >= mA and mH> 125.:
        logger.info("MA_{} =< MH_{} switching to H->ZA mode!".format(mA, mH))
        mode = 'H'
    elif mH >= mA and mH <= 125.:
        logger.info("MA_{} >= MH_{} && H <= 125. GeV switching to h->ZH mode!".format(mA, mH))
        mode ='h'
    sqrts = 13000
    type = 2
    mh = mh
    cba = 0.01  #  cos( beta -alpha) " should not be changed: that's the alignement limit 
    alpha=math.atan(tb)-math.acos(cba)
    sinbma = math.sin(math.atan(tb)-alpha)
    #sinbma = math.sqrt(1 - pow(cba, 2))
    mhc = max(mH, mA)
    m12 = math.sqrt(pow(mhc, 2) * tb / (1 + pow(tb, 2)))
    outputFile = 'madgraphInputs_mH-{}_mA-{}_tb-{}.dat'.format(mass_to_string(mH), mass_to_string(mA), mass_to_string( tb))
    cwd = os.getcwd()
    print("Moving to {} to call ./2HDMC-1.7.0/CalcPhys".format(CMSSW_Calculators42HDM))
    os.chdir(CMSSW_Calculators42HDM)
    res = Calc2HDM(mode = mode, sqrts = sqrts, type = type,
                   tb = tb, m12 = m12, mh = mh, mH = mH, mA = mA, mhc = mhc, sba = sinbma,
                   outputFile = outputFile, muR = 1., muF = 1.)
    res.setpdf(pdfName)
    res.computeBR()
    wH = float(res.Hwidth)
    wA = float(res.Awidth)
    l2 = float(res.lambda_2)
    l3 = float(res.lambda_3)
    lR7 = float(res.lambda_7)
    AtoZhBR = res.AtoZhBR
    AtobbBR = res.AtobbBR
    HtoZABR = res.HtoZABR
    HtobbBR = res.HtobbBR
    os.chdir(cwd)
    return wH, wA, l2, l3, lR7, sinbma, tb #, AtoZhBR, AtobbBR, HtoZABR, HtobbBR

processes = {
    "ggH" : ["# gg fusion loop-induced",
        "generate p p > h2 > h3 Z [QCD] @0"
        ],
    "bbH4F": ["# bb-associated production: 4flavor scheme",
        "generate p p > h2 > h3 Z b b~ [QCD] @0"
        ]
    }

def prepare_cards(mH, mA, mh, wH, wA, l2, l3, lR7, sinbma, tb, process=None,
        lhaid='$DEFAULT_PDF_SETS', templateDir=None, outputDir=None, name=None):
    cardsDir = os.path.join(outputDir, name)
    if not os.path.exists(cardsDir):
        os.makedirs(cardsDir)
    # customizecards
    with open(os.path.join(cardsDir, "{}_customizecards.dat".format(name)), 'w+') as outf:
        outf.write("\n".join(
            " ".join(("set param_card", param,
                ## 2 decimal digits for mass, else 6; if not float: directly
                (("{:.2f}" if "mass" in param else "{:.6f}").format(value)
                if isinstance(value, float) else value),
                comment))
            for param, value, comment in [
                ("higgs 1"  ,     l2, "lambda 2"),
                ("higgs 2"  ,     l3, "lambda 3"),
                ("higgs 3"  ,    lR7, "lambda Real 7"),
                ("mass 25"  ,     mh, "mh"),
                ("mass 35"  ,     mH, "mA"),
                ("mass 36"  ,     mA, "mH"),
                ("width 36" , "Auto", "wA"),
                ("width 35" ,     wH, "wH"),
                ("frblock 1",     tb, "tb"),
                ("frblock 2", sinbma, "sinbma"),
                ]))
    # extramodels, just two lines
    with open(os.path.join(cardsDir, "{}_extramodels.dat".format(name)), 'w') as outf:
        outf.write("\n".join((
            "# http://feynrules.irmp.ucl.ac.be/attachment/wiki/2HDM/2HDMtII_NLO.tar.gz",
            "2HDMtII_NLO.tar.gz"
            )))
    # proc_card: change the output name
    with open(os.path.join(cardsDir, "{}_proc_card.dat".format(name)), 'w') as outf:
        outf.write("\n".join([
            "import model 2HDMtII_NLO"]+
            processes[process]+[
            "output {} -nojpeg".format(name)
            ]))
    # run card: change the PDF if needed
    with open(os.path.join(templateDir, process, "run_card.dat"), 'r') as inf:
        with open(os.path.join(cardsDir, "{}_run_card.dat".format(name)), 'w') as outf:
             for line in inf:
                 if 'lhaid' in line:
                     outf.write('{} = lhaid ! if pdlabel=lhapdf, this is the lhapdf number\n'.format(lhaid))
                     if lhaid is '$DEFAULT_PDF_SETS':
                         outf.write('$DEFAULT_PDF_MEMBERS  = reweight_PDF\n')
                 else:
                     outf.write(line)
    print('MG5 files prepared in {}'.format(cardsDir))

def prepare_all_MG5_cards(process=None, flavourScheme="4F", lhapdfsets=None, lhaid=None,
                          queue="1nh", test=False, templateDir=None, gridpointsdata=None):
    grids = makeGridPoints(gridpointsdata)
    if test:
        outputdir = "example_cards"
        griddata = "example_card"
        suffix = "example"
        if process == "ggH":
            tb_list = [1.5]
        else:
            tb_list = [20.0]
    else:
        outputdir = "PrivateProd_run2"
        griddata = "fullsim"
        suffix = "all"
        tb_list = [0.5,1.0,1.5,2.0,5.0,6.0,8.0,10.0,15.0,20.0,30.0,40.0,50.0]

    mh=125.
    if process == "ggH":
        smpdetails = "ggH_TuneCP5_13TeV_pythia8" ## loop-induced and 4F in any case
    else:
        if flavourScheme == "4F":
            process = "".join((process, flavourScheme))
        smpdetails = "{}_TuneCP5_13TeV-amcatnlo_pythia8".format(process)

    pdfName, lhaid = getLHAPDF(lhapdfsets=lhapdfsets, lhaid=lhaid, scheme=flavourScheme)

    mAmHtanBpoints = []
    for H, A in grids[griddata]:
        mH = float_to_mass(H)
        mA = float_to_mass(A)
        #FIXME : I DON'T SEE A RASON FOR SKIPPING THESE POINTS
        #if mH < 125.:
        #    s = '# skipping point (mH, mA) = ({}, {})'.format(mH, mA)
        #    print (s)
        #    outf.write(s + '\n')
        #    continue
        for tb in tb_list:
            wH, wA, l2, l3, lR7, sinbma, tb = compute_widths_BR_and_lambdas(mH, mA, mh, tb, pdfName=pdfName)

            procname = "HToZATo2L2B_{}_{}".format("_".join(mass_to_string(mm) for mm in (mH, mA, tb)), smpdetails)
            prepare_cards(mH, mA, mh, wH, wA, l2, l3, lR7, sinbma, tb,
                    process=process, name=procname, lhaid=lhaid,
                    templateDir=templateDir, outputDir=outputdir)
            mAmHtanBpoints.append(procname)

    writeScript(mAmHtanBpoints, os.path.join(outputdir, 'prepare_{}_{}_gridpacks.sh'.format(suffix, process)), test=test, queue=queue)

def writeScript(procNames, outName, test=False, queue="1nh"):
    with open(outName, 'w+') as outf:
        outf.write("\n".join([
            '## NOTE: this script was generated by prepare_MG5_cards.py for your convenience',
            '## It should be run from the genproductions/bin/MadGraph5_aMCatNLO directory in a clean environment,',
            '## and will submit the gridpack generation for all points.',
            'cardsdir=$(dirname $0)',
            'echo "Using the cards in ${cardsdir}"'
            ]+([ './submit_condor_gridpack_generation.sh' ] if 'condor' in queue
                else [
                    '# kEEP IN MIND : IF You are submitting from lxplus and the local directory is not on AFS',
                    '# Automatically will switch to condor spool mode.'
                    '# So you have to call : ./submit_condor_gridpack_generation.sh'
            ])+[ " ".join(("./gridpack_generation.sh", name, '"${{cardsdir}}/{}"'.format(name), queue)) for name in procNames
            ]))
    os.chmod(outName, os.stat(outName).st_mode | stat.S_IXUSR)
    print('All commands prepared in {}'.format(outName))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Preparing Grid Pack for 2HDM H/A-> Z(->ll) A/H(->bb) for full run2 Ultra Legacy Campaigns', formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-q', '--queue', default='1nh', choices=['condor', 'condor_spool', '1nh'],
            help='more options : [pbs|sge|condor|lsf|ge|slurm|htcaas|htcaas2] Use for cluster run only')
    parser.add_argument('--process', required=True, choices=["ggH", "bbH"], help="Loop-induced gg->H (LO) or bbH (NLO)")
    parser.add_argument('--flavourscheme', default="4F", choices=["4F", "5F"], help="Pass 5F to use the 5-flavour scheme")
    parser.add_argument('--templates', required=True, help="Directory with run card templates for all processes")
    parser.add_argument("--gridpoints", default="./data", help="Directory with grid points data in JSON format")
    parser.add_argument('--test', action='store_true', help='Generate 1 set of cards stored by default in  example_cards/')
# If you are not sure about your pdf sets setting, better use DEFAULT !
    parser.add_argument('-pdf', '--lhapdfsets', default='DEFAULT', help=(
        'Few links may help you to make the choice:\n'
        'https://twiki.cern.ch/twiki/bin/view/CMS/QuickGuideMadGraph5aMCatNLO#PDF_Choice_for_2017_production\n'
        'https://monte-carlo-production-tools.gitbook.io/project/mccontact/info-for-mc-production-for-ultra-legacy-campaigns-2016-2017-2018'))
    parser.add_argument('--lhaid', type=int, help = 'LHAPDF ID(ver 6.3.0) : Full list here : https://lhapdf.hepforge.org/pdfsets')
    options = parser.parse_args()

    prepare_all_MG5_cards(process=options.process, flavourScheme=options.flavourscheme, lhapdfsets=options.lhapdfsets, lhaid=options.lhaid, test=options.test, queue=options.queue, gridpointsdata=options.gridpoints, templateDir=options.templates)
