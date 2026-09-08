# Meta-Completion Kilobot firmware

This repository contains the paper firmware snapshot finalised on 29 August
2026.  It separates the three task mechanisms (battery, random walk, and
voting) from the method used to detect system-level completion.

## Repository contents

- `firmware/centralised/`: task firmware used with the external centralised
  observer.  The observer is outside the Kilobot firmware.
- `firmware/lmc/`: Linear Meta-Consensus (LMC) firmware.
- `firmware/flooding/`: strict full-table flooding firmware and the separately
  labelled five-UID positive control.
- `notebooks/`: location for the exported Colab simulation notebooks.

The older `dropout`, `broken`, and experimental files from the development
directory are intentionally excluded from this final snapshot.

## Final experimental settings

| Task | Local completion rule | LMC parameters |
|---|---|---|
| Battery | Start at 0; increase by 1 every second; complete at 100 | `k1=0.50`, `k2=0.43`, threshold `P>=0.99` |
| Random walk | Move for a random 5--15 s; make one random left/right turn lasting 16 ticks (about 0.5 s); then stop | `k1=0.50`, `k2=0.48`, threshold `P>=0.99` for 10 consecutive LMC updates |
| Voting | Start with random opinion A/B; complete after 10 consecutive received messages agreeing with the current opinion; a different opinion is adopted and resets completion | `k1=0.50`, `k2=0.43`, threshold `P>=0.99` |

All communicating programs schedule a new transmission no faster than once
every 8 Kilobot ticks (nominally 0.25 s at 32 ticks/s) and wait for the
previous transmission to succeed.  Actual successful transmission times also
depend on Kilobot collision avoidance.

The two files ending in `_slow.c` are the deliberately unfinished robots used
in partial-completion trials.  They remain stationary with `s=0` and `P=0`,
show red, and continue transmitting `P=0` at the same communication interval.

Strict flooding requires records for all 100 UIDs and requires every stored
completion state to be 1.  Battery and random-walk completion are monotonic;
Voting uses versioned records because its completion state is reversible.

`Battery_flooding_5uid_control.c` is only a positive control.  It turns blue
after five distinct UIDs have been collected, confirming reception, table
merging, forwarding, counting, and LED triggering.  It does **not** test or
claim full-swarm completion.

## Building

The source targets the ATmega328P and the Kilobot `kilolib` API.  Copy a source
file into a kilolib checkout and build it with the AVR toolchain, for example:

```sh
make build/Battery_LMC.hex
```

An AVR GCC toolchain is required.  Precompiled `.hex` files are deliberately
not included so that binaries cannot be confused with older experimental
builds.

## Simulation notebooks

For reproducibility, export every final Google Colab notebook as `.ipynb` and
commit it under `notebooks/`.  A Colab share link or an “Open in Colab” badge
can also be supplied for convenience, but should not be the only copy because
Drive permissions and notebook contents can change.  For a paper release,
archive the tagged GitHub version (for example through Zenodo) so the submitted
code has a fixed version and DOI.
