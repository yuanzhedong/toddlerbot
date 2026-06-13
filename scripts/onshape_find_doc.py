"""Verify Onshape API keys and find a document by name.

Reads ONSHAPE_API / ONSHAPE_ACCESS_KEY / ONSHAPE_SECRET_KEY from the environment
(source your .env first), authenticates, and searches your Onshape documents for
a name substring. Prints each match's document id + default workspace + assemblies
so you can plug the id into the onshape-to-robot pipeline.

Usage:
    set -a && source .env && set +a
    python scripts/onshape_find_doc.py --name "ToddlerBot - 3.0"
"""

import argparse
import json
import os
import tempfile

from onshape_to_robot.onshape_api.onshape import Onshape


def client():
    # Onshape() requires a creds file to *exist*; if it lacks the keys it falls
    # back to env vars. So hand it an empty JSON and let the env drive auth.
    tf = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    json.dump({}, tf)
    tf.close()
    return Onshape(stack=os.environ["ONSHAPE_API"], creds=tf.name, logging=False)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--name", default="ToddlerBot - 3.0", help="document name substring")
    args = p.parse_args()

    c = client()
    # Authenticated search across documents you can access.
    resp = c.request(
        "get", "/api/documents", query={"q": args.name, "filter": 0, "limit": 20}
    )
    docs = resp.json().get("items", [])
    print(f"Auth OK. {len(docs)} document(s) matching '{args.name}':\n")
    for d in docs:
        did = d["id"]
        wid = (d.get("defaultWorkspace") or {}).get("id", "?")
        print(f"  name : {d['name']}")
        print(f"  doc  : {did}")
        print(f"  wspace: {wid}")
        # List assembly elements in the default workspace.
        try:
            els = c.request("get", f"/api/documents/d/{did}/w/{wid}/elements").json()
            asms = [e["name"] for e in els if e.get("elementType") == "ASSEMBLY"]
            print(f"  assemblies: {asms}")
        except Exception as e:  # noqa: BLE001
            print(f"  (could not list elements: {e})")
        print()


if __name__ == "__main__":
    main()
