# H->ZA->llbb gridpacks production:

## Preparing the cards

This needs 2HDMC, which is a general-purpose calculator for the two-Higgs doublet model.
It allows parametrization of the Higgs potential in many different ways,
convenient specification of generic Yukawa sectors,
the evaluation of decay widths (including higher-order QCD corrections),
theoretical constraints and much more.

You can install Calculators42HDM in a CMSSW release (recommended)
or a conda environment (which requires a few changes to the script),
see the [installation instructions](https://github.com/kjaffel/Calculators42HDM/blob/master/README.md).

In that environment the [``prepare_MG5_cards.py``](prepare_MG5_cards.py)
that is included here can be used to generate the cards, with
```bash
./prepare_MG5_cards.py --process=bbH --test
```
The script needs two additional arguments:
- ``--templates``: a directory with run cards for the two processes, each in a subdirectory
  with their name (which should include ``4FS`` or ``5FS`` for bb-associated production)
- ``--gridpoints``: a directory with the JSON files with (mA, mH) points definitions

Other optional arguments are:
- ``-q``/``--queue``: condor queue
- ``--test`` will produce 1 set of cards for each process, saved by default in ``example_cards/``
- ``--lhaid`` will be set to `$DEFAULT_PDF_SETS` as shortcuts to have the PDF sets automatically
  and added to the ``run_card`` at run time to avoid specifying them directly
  ```
  lhapdf = pdlabel ! PDF set
  $DEFAULT_PDF_SETS = lhaid
  $DEFAULT_PDF_MEMBERS  = reweight_PDF
  ```

## Generating the gridpacks

Inside the cards output directory (``example_cards`` or ``PrivateProd_run2``)
a simple shell script is generated to produce all the gridpacks.
It should be run from the ``genproductions/bin/MadGraph5_aMCatNLO`` directory,
in a clean environment.
