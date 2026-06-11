"""Run once to inspect the existing Notion DB schema."""
import os
from dotenv import load_dotenv
from notion_client import Client

load_dotenv(dotenv_path="../.env")


def main():
    token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or NOTION_DATABASE_ID missing in .env")
        return

    notion = Client(auth=token)

    try:
        db = notion.databases.retrieve(database_id=db_id)
    except Exception as e:
        print(f"ERROR connecting to Notion: {e}")
        return

    title = db["title"][0]["plain_text"] if db["title"] else "(sans titre)"
    print(f"\nBase : {title}\n")
    print(f"{'Nom':<30} {'Type':<20} {'Valeurs (si select)'}")
    print("-" * 80)

    for name, prop in db["properties"].items():
        ptype = prop["type"]
        values = ""
        if ptype in ("select", "multi_select"):
            options = prop[ptype]["options"]
            values = ", ".join(o["name"] for o in options)
        print(f"{name:<30} {ptype:<20} {values}")


main()
