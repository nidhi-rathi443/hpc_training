#!/bin/bash

echo "Building hpl with aocc"

source modules/aocc.sh

case "hpl" in
  hpl)
    cd $HOME/hpl-2.3 && make
    cp bin/*/xhpl $SLURM_SUBMIT_DIR/benchmarks/hpl/aocc/
    ;;
  hpcg)
    cd $HOME/hpcg-HPCG-release-3-1-0 && make
    cp bin/*/xhpcg $SLURM_SUBMIT_DIR/benchmarks/hpcg/aocc/
    ;;
  stream)
    cd $HOME/STREAM && make
    cp stream $SLURM_SUBMIT_DIR/benchmarks/stream/aocc/
    ;;
esac

echo "Build completed for hpl (aocc)"
