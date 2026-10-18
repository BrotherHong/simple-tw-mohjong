"""Select a reproducible mutant sample without running any tests."""

import argparse
from collections import defaultdict
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
from random import Random
import tempfile

from cosmic_ray.work_db import WorkDB, use_db


ROOT = Path(__file__).resolve().parents[1]


def positive_integer(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Must be a positive integer.")
    return number


def mutation_key(item):
    mutation = item.mutations[0]
    return json.dumps(
        [mutation.module_path.as_posix(), mutation.operator_name,
         mutation.occurrence, mutation.start_pos, mutation.end_pos,
         mutation.operator_args],
        sort_keys=True,
    )


def prepare_sample(source, output, per_module, seed):
    source, output = (ROOT / source).resolve(), (ROOT / output).resolve()
    manifest = output.with_suffix(".json")
    if output.suffix != ".sqlite":
        raise ValueError("The output must have a .sqlite extension.")
    if source in (output, manifest):
        raise ValueError("Source and output paths must differ.")
    if output.exists() or manifest.exists():
        raise FileExistsError("Sample output already exists; refusing to overwrite.")
    if per_module < 1:
        raise ValueError("per_module must be positive.")
    if version("cosmic-ray") != "8.7.0":
        raise ValueError("This sampler requires Cosmic Ray 8.7.0.")
    if any(Path(str(source) + suffix).exists() for suffix in ("-wal", "-shm", "-journal")):
        raise ValueError("Close and checkpoint the source database first.")

    # Read a snapshot so Cosmic Ray never opens the original database for writing.
    source_bytes = source.read_bytes()
    cache = ROOT / ".cache"
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=cache) as temporary:
        snapshot = Path(temporary) / "source.sqlite"
        snapshot.write_bytes(source_bytes)
        with use_db(snapshot, mode=WorkDB.Mode.open) as database:
            if database.num_results:
                raise ValueError("The source session must not contain results.")
            items = database.work_items
        if not items:
            raise ValueError("The source session has no mutants.")

        groups = defaultdict(list)
        for item in items:
            if len(item.mutations) != 1:
                raise ValueError("Only single-mutation work items are supported.")
            groups[item.mutations[0].module_path.as_posix()].append(item)

        selected, counts = [], {}
        rng = Random(seed)
        for module, candidates in sorted(groups.items()):
            candidates.sort(key=mutation_key)
            # Shuffle the full group so larger samples retain smaller samples.
            rng.shuffle(candidates)
            chosen = sorted(candidates[:per_module], key=mutation_key)
            selected.extend(chosen)
            counts[module] = {"available": len(candidates), "selected": len(chosen)}

        sampled = Path(temporary) / "sample.sqlite"
        with use_db(sampled) as database:
            database.add_work_items(selected)
        details = {
            "cosmic_ray_version": "8.7.0",
            "seed": seed,
            "per_module": per_module,
            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
            "total": len(selected),
            "modules": counts,
            "selected_job_ids": [item.job_id for item in selected],
        }

        # Exclusive creation protects existing sessions and manifests.
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as handle:
            handle.write(sampled.read_bytes())
        with manifest.open("x", encoding="utf-8") as handle:
            json.dump(details, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

    for module, count in counts.items():
        print(f"{module}: {count['selected']} / {count['available']}")
    print(f"Selected {len(selected)} mutants: {output}")
    print(f"Manifest: {manifest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("mutation/all-mutants.sqlite"))
    parser.add_argument("--output", type=Path, default=Path("mutation/sampled-mutants.sqlite"))
    parser.add_argument("--per-module", type=positive_integer, default=50)
    parser.add_argument("--seed", type=int, default=20261019)
    args = parser.parse_args()
    try:
        prepare_sample(args.source, args.output, args.per_module, args.seed)
    except Exception as error:
        parser.exit(1, f"Sampling failed: {error}\n")


if __name__ == "__main__":
    main()
