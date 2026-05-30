import os
import glob
import re
import pyfabricops as pf

from utils import list_changed_src_items

from dotenv import load_dotenv

from pathlib import Path 

# Load environment variables from .env file or environment
load_dotenv()
pf.set_auth_provider("env")

# Set up logging
pf.setup_logging("info", "standard")
logger = pf.get_logger(__name__)

# Determine deployment mode and items to deploy
mode = os.getenv("DEPLOY_MODE") or "selective" # "selective", "specific", "full"

specific_items = os.getenv("ITEMS_TO_DEPLOY", "") # Comma-separated list of specific items to deploy when DEPLOY_MODE is "specific" 

branch = os.getenv("BUILD_SOURCEBRANCHNAME") or pf.get_current_branch()


# Variables 
root_path = Path("src")
vl_path = root_path / "CICD" / "EnvironmentVariables.VariableLibrary"

def _get_merged_config(branch):
    defaults = {
        v["name"]: v
        for v in pf.read_json(vl_path / "variables.json").get(
            "variables", []
        )
    }
    overrides = {
        v["name"]: v
        for v in pf.read_json(
            vl_path / "valueSets" / f"{branch}.json"
        ).get("variableOverrides", [])
    }
    return list({**defaults, **overrides}.values())


config = _get_merged_config(branch)

workspace_id = next(
    (item.get("value") for item in config if item.get("name") == "workspace_id"), None
)

if workspace_id is None:
    raise ValueError("workspace_id not found in variables.json or variableOverrides")

workspace_name = pf.get_workspace(workspace_id, df=False).get("displayName")

if workspace_name is None:
    raise ValueError(f"Workspace with ID {workspace_id} not found")

if mode.lower() == "full":
    logger.info(
        f"Deploying all items to workspace: {workspace_name} (ID: {workspace_id})"
    )
else:
    logger.info(
        f"Deploying only changed items to workspace: {workspace_name} (ID: {workspace_id})"
    )

if mode.lower() == "full":
    platform_files = glob.glob("src/**/.platform", recursive=True)
    items = sorted({os.path.dirname(path) for path in platform_files})
elif mode.lower() == "specific":
    items = [item.strip() for item in specific_items.split(",") if item.strip()]
else:
    items = list_changed_src_items(src_root="src")

if not items:
    logger.info("No items to deploy")
    exit(0)

items_qty = len(items)

logger.info(f"Found {items_qty} items to deploy:")

logger.info(items)


def _resolve_config(vl_path, branch):
    """Merge variables.json defaults with valueSet overrides for the given branch."""
    defaults = {
        v["name"]: v
        for v in pf.read_json(vl_path / "variables.json").get("variables", [])
    }
    overrides = {
        v["name"]: v
        for v in pf.read_json(vl_path / "valueSets" / f"{branch}.json").get(
            "variableOverrides", []
        )
    }
    merged = {**defaults, **overrides}
    return list(merged.values())


config_from = _resolve_config(vl_path, "develop")
config_to = config if branch != "develop" else config_from

# Switch lakehouses in notebooks before deployment (if any notebooks are in the list of items to deploy)
notebooks = [item for item in items if item.endswith(".Notebook")]
if len(notebooks) > 0:
    logger.info(f"Found {len(notebooks)} notebooks to process for lakehouse switching")

    target_variables = [
        "workspace_id",
        "lakehouse_bronze",
        "lakehouse_silver",
        "lakehouse_gold",
    ]

    replacements = {}

    for var in target_variables:
        raw_from = next(
            (item.get("value") for item in config_from if item.get("name") == var), None
        )
        raw_to = next(
            (item.get("value") for item in config_to if item.get("name") == var), None
        )

        if raw_from is None or raw_to is None:
            logger.warning(f"Variable '{var}' not found in one of the configs")
            continue

        value_from = raw_from.get("itemId") if isinstance(raw_from, dict) else raw_from
        value_to = raw_to.get("itemId") if isinstance(raw_to, dict) else raw_to

        find_pattern = rf"(?i){re.escape(value_from)}"
        replacements[(r".*\.py$", find_pattern)] = value_to

    for nb in notebooks:
        logger.info(f"Processing notebook: {nb}")
        pf.find_and_replace(nb, replacements)


# Switching semantic models parameters before deployment (if any semantic models are in the list of items to deploy)
semantic_models = [item for item in items if item.endswith(".SemanticModel")]

if len(semantic_models) > 0:
    logger.info(
        f"Found {len(semantic_models)} semantic models to process for parameter switching"
    )

    target_variables = [
        "workspace_id",
        "lakehouse_gold",
    ]

    replacements = {}

    for var in target_variables:
        raw_from = next(
            (item.get("value") for item in config_from if item.get("name") == var), None
        )
        raw_to = next(
            (item.get("value") for item in config_to if item.get("name") == var), None
        )

        if raw_from is None or raw_to is None:
            logger.warning(f"Variable '{var}' not found in one of the configs")
            continue

        value_from = raw_from.get("itemId") if isinstance(raw_from, dict) else raw_from
        value_to = raw_to.get("itemId") if isinstance(raw_to, dict) else raw_to

        find_pattern = rf"(?i){re.escape(value_from)}"
        replacements[(r".*expressions\.tmdl$", find_pattern)] = value_to

    for sm in semantic_models:
        logger.info(f"Processing semantic model: {sm}")
        pf.find_and_replace(sm, replacements)

items_deployed = []

# Deploy items except reports
items_to_deploy = [item for item in items if not item.endswith(".Report")]
for item in items_to_deploy:
    logger.info(f"Deploying item: {item}")
    deployed_item = pf.deploy_item(workspace_id, item, start_path="src", df=False)
    if deployed_item is not None:
        logger.success(f"Successfully deployed item: {item}")
    items_deployed.append(deployed_item)


# Deploy reports separately to utilize report definition conversion before deployment
reports = [item for item in items if item.endswith(".Report")]
for report in reports:
    logger.info(f"Deploying report: {report}")
    pf.convert_report_definition_to_by_connection(workspace_name, report)
    deployed_report = pf.deploy_item(workspace_id, report, start_path="src", df=False)
    if deployed_report is not None:
        logger.success(f"Successfully deployed report: {report}")
    items_deployed.append(deployed_report)


items_deployed_qty = len(items_deployed)
if items_deployed_qty == items_qty:
    logger.success(f"Successfully deployed all {items_deployed_qty} items")
else:
    logger.warning(f"Deployed {items_deployed_qty} out of {items_qty} items")
