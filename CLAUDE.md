# Tuikio: start here

Read `docs/handoff/README.md` first, then `docs/handoff/RULES.md`. Together they explain what
Tuikio is, the owner's rules (security, licences, honesty, no publishing without approval, games
offline and without a shell), how to build, test and release, the current state and the next
steps. `docs/handoff/PLAYBOOK.md` has step-by-step recipes (port a game, audit, card art,
release); `docs/handoff/LESSONS.md` lists the traps already hit.

Quick checks before any push:

    ./gradlew :tools:catalog-cli:run --args="validate $PWD/catalog"
    python3 tools/catalog/gen_credits.py --check
    ./gradlew :core:controls:test :core:catalog:test
    ./gradlew :core:runtime:test -PrequireNative   # after python3 native/build.py

The owner writes mostly in Turkish: answer in their language, results first, briefly.
