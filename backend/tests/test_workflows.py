import json
from pathlib import Path


WORKFLOW_DIR = Path(__file__).resolve().parents[1] / "workflows"


def test_all_crm_webhook_nodes_send_service_secret():
    webhook_nodes = []
    for workflow_path in WORKFLOW_DIR.glob("*.workflow.json"):
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        for node in workflow.get("nodes", []):
            parameters = node.get("parameters", {})
            if "/webhooks/" in parameters.get("url", ""):
                webhook_nodes.append((workflow_path.name, node.get("name"), parameters))

    assert webhook_nodes
    for workflow_name, node_name, parameters in webhook_nodes:
        assert parameters.get("sendHeaders") is True, f"{workflow_name}: {node_name} does not send headers"
        headers = parameters.get("headerParameters", {}).get("parameters", [])
        assert {
            "name": "X-CRM-Webhook-Secret",
            "value": "={{$env.CRM_WEBHOOK_SECRET}}",
        } in headers, f"{workflow_name}: {node_name} is missing webhook authentication"
