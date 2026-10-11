# Piskvork
Play Gomoku (five in a row) game against the best in the world AIs which can be downloaded from https://gomocup.org/. 
- time limits (difficulty) can be changed anytime during match
- unlimited undo, redo
- log window shows coordinates and time of every move
- 12 skins, users can add their own skins
- Renju rule
- Caro rule (Gomoku+)

You can **download** released binaries (EXE file) for Windows from [sourceforge.net](https://sourceforge.net/projects/piskvork/).

![Piskvork screenshot](https://plastovicka.github.io/img/pisvork-gomo-cz.png)
![Piskvork screenshot](https://plastovicka.github.io/img/piskvork.png)

## Reproducible command-line benchmarks

`-size N` sets a square board before board/window initialization (5–80).
`-no-registry` ignores saved user settings and disables settings/toolbar writes.
`-benchmark` implies `-no-registry` and enables fixed openings, enforced timeouts,
zero timeout tolerance, normal colors and engine suspension between turns. It
turns off random opening transforms, continuous games, pondering/debug mode,
sounds and completion commands. Requires `-p` or the settings diagnostic below.
Existing `-rule`, time, memory, opening, affinity and log arguments remain available.
Invalid new options exit with code 64 before windows or engines start.
Without these new switches the interactive application's behavior is unchanged.

Example standard match (exactly five wins; 15×15; five seconds per move):

```
piskvork.exe -benchmark -size 15 -p first.exe second.exe -rule 1 -timeturn 5000 -timematch 120 -memory 1024 -opening 0 -outfile game.psq
```

Use `-size 20 -rule 0` for freestyle. Supply the appropriate `openings.txt` beside
the executable. A benchmark process never persists these choices in HKCU.
`-print-settings settings.json` writes effective match settings and exits without
opening a window or starting engines; it can be combined with the switches above.
Exit 65 indicates a diagnostic output-file error. Existing match result codes
remain 1/2 for first/second player winning and 3 for a draw.

## GitHub build artifact

The Build Piskvork workflow runs on pushes, PRs and manual dispatch on GitHub's
Windows runner. It builds only `source/piskvork.vcxproj` (Release x64, v143, static
C++ runtime), tests CLI parsing and registry isolation with no engine matches,
and uploads `piskvork-windows-x64`. The artifact contains the executable, language
and skin resources, opening file, documentation and `build.json` with source
commit, run ID, CLI capability version and executable SHA-256. No release is made.