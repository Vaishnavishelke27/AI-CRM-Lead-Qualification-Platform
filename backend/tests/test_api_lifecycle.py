import asyncio
import os

from httpx import ASGITransport, AsyncClient

from app.main import app, process_import_job
from app.models import ImportJob


def test_complete_lead_task_email_lifecycle(db):
    async def exercise_api():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            registration = await client.post(
                "/auth/register",
                json={"email": "owner@example.com", "full_name": "CRM Owner", "password": "password123"},
            )
            assert registration.status_code == 201

            login = await client.post(
                "/auth/login",
                json={"email": "owner@example.com", "password": "password123"},
            )
            assert login.status_code == 200
            headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

            created_lead = await client.post(
                "/leads",
                headers=headers,
                json={
                    "name": "Lifecycle Lead",
                    "email": "lifecycle@example.com",
                    "company": "Example Co",
                    "source": "referral",
                    "lead_score": 80,
                },
            )
            assert created_lead.status_code == 201
            lead = created_lead.json()
            assert lead["category"] == "Hot"

            enrichment = await client.post(
                "/webhooks/lead-enrichment",
                headers={"X-CRM-Webhook-Secret": os.environ["CRM_WEBHOOK_SECRET"]},
                json={"lead_id": lead["id"], "context": {}},
            )
            assert enrichment.status_code == 200

            listed_leads = await client.get("/leads", headers=headers)
            assert [item["id"] for item in listed_leads.json()] == [lead["id"]]

            updated_lead = await client.put(
                f"/leads/{lead['id']}",
                headers=headers,
                json={"status": "qualified"},
            )
            assert updated_lead.status_code == 200
            assert updated_lead.json()["status"] == "qualified"

            manually_assigned_lead = await client.put(
                f"/leads/{lead['id']}",
                headers=headers,
                json={"assigned_to": "account-owner@example.com"},
            )
            assert manually_assigned_lead.status_code == 200
            assert manually_assigned_lead.json()["assigned_to"] == "account-owner@example.com"

            workflow_assignment = await client.post(
                "/webhooks/update-lead",
                headers={"X-CRM-Webhook-Secret": os.environ["CRM_WEBHOOK_SECRET"]},
                json={"lead_id": lead["id"], "assigned_to": "workflow-owner@example.com"},
            )
            assert workflow_assignment.status_code == 200
            assert workflow_assignment.json()["lead"]["assigned_to"] == "workflow-owner@example.com"

            created_task = await client.post(
                "/tasks",
                headers=headers,
                json={"lead_id": lead["id"]},
            )
            assert created_task.status_code == 201
            task = created_task.json()
            assert task["description"]

            completed_task = await client.put(
                f"/tasks/{task['id']}",
                headers=headers,
                json={"status": "completed"},
            )
            assert completed_task.json()["status"] == "completed"

            generated_email = await client.post(
                "/emails/generate",
                headers=headers,
                json={"lead_id": lead["id"], "purpose": "follow_up"},
            )
            assert generated_email.status_code == 201
            assert generated_email.json()["tracking_token"]

            emails = await client.get("/emails", headers=headers)
            assert len(emails.json()) == 1

            deleted = await client.delete(f"/leads/{lead['id']}", headers=headers)
            assert deleted.status_code == 204
            assert (await client.get("/leads", headers=headers)).json() == []
            assert (await client.get("/tasks", headers=headers)).json() == []
            assert (await client.get("/emails", headers=headers)).json() == []

    asyncio.run(exercise_api())


def test_import_job_state_is_persisted(db):
    job = ImportJob(
        job_id="persistent-job",
        status="queued",
        user_email="manager@example.com",
        filename="leads.csv",
    )
    db.add(job)
    db.commit()

    asyncio.run(process_import_job("persistent-job", "name,email\nImported Lead,imported@example.com\n"))

    db.expire_all()
    persisted = db.get(ImportJob, "persistent-job")
    assert persisted.status == "completed"
    assert persisted.result == {"created": 1, "skipped": []}
