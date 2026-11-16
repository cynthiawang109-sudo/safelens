"""Explicit offline indexing and report-level search commands."""

import argparse
import json
import logging
from dataclasses import asdict, replace

import psycopg

from safelens.config import Settings
from safelens.embed import LocalEmbeddingProvider
from safelens.reindex import reindex
from safelens.retrieve import (
    RetrievalConfig,
    search_dense,
    search_hybrid,
    search_lexical,
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("reindex")
    build.add_argument("--model")
    build.add_argument("--revision")
    build.add_argument("--dimension", type=int)
    build.add_argument("--subset-manifest", "--corpus-manifest", dest="subset_manifest", help="Verified corpus manifest")
    build.add_argument("--incremental", action="store_true", help="Reuse unchanged indexed reports; permit growth but no deletion")
    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--method", choices=["lexical", "dense", "hybrid", "all"], default="all")
    search.add_argument("-k", type=int, default=5)
    search.add_argument("--category", default=None)
    search.add_argument("--candidate-chunks", type=int, default=100)
    search.add_argument("--candidate-reports", type=int, default=50)
    args = parser.parse_args()
    settings = Settings.from_env()
    logging.basicConfig(level=logging.INFO)
    with psycopg.connect(settings.database_url, autocommit=True, connect_timeout=10) as conn:
        if args.command == "reindex":
            if args.model and args.model != settings.embedding_model and not args.revision:
                parser.error("A different model requires an explicit --revision (and matching --dimension)")
            settings = replace(settings, embedding_model=args.model or settings.embedding_model,
                               embedding_revision=args.revision or settings.embedding_revision,
                               embedding_dim=args.dimension or settings.embedding_dim)
            replacement = None
            if args.subset_manifest:
                from pathlib import Path
                manifest = json.loads(Path(args.subset_manifest).read_text(encoding="utf-8"))
                if manifest.get("manifest_type") == "flagship_year_stratified_v1":
                    from safelens.corpus import load_expanded_reports
                    replacement = load_expanded_reports(args.subset_manifest)
                else:
                    from safelens.subset import load_manifest_reports
                    replacement = load_manifest_reports(args.subset_manifest)
            print(json.dumps(reindex(conn, settings, LocalEmbeddingProvider,
                                     replacement_reports=replacement, incremental=args.incremental), indent=2))
        else:
            config = RetrievalConfig(args.candidate_chunks, args.candidate_reports)
            provider = None if args.method == "lexical" else LocalEmbeddingProvider(settings)
            results = {}
            for name, function in (("lexical", search_lexical), ("dense", search_dense), ("hybrid", search_hybrid)):
                if args.method not in ("all", name):
                    continue
                options = {} if name == "lexical" else {"provider": provider}
                results[name] = function(args.query, args.k, conn=conn, settings=settings,
                                         category=args.category, config=config, **options)
            print(json.dumps({"query": args.query, "retrieval_config": asdict(config),
                              "category": args.category, "results": results}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
