from __future__ import annotations

USER_AGENT = "ClioAug22Build/0.1 (+Quinn Rodriguez Law)"

DEFAULT_FIELDS: dict[str, str] = {
    "who_am_i": (
        "id,etag,name,first_name,last_name,email,enabled,subscription_type,"
        "time_zone,roles"
    ),
    "contacts": (
        "id,etag,name,first_name,last_name,type,primary_email_address,"
        "primary_phone_number,company{id,name},created_at,updated_at"
    ),
    "matters": (
        "id,etag,display_number,number,description,status,open_date,close_date,"
        "client{id,name},responsible_attorney{id,name},billable,billing_method,"
        "practice_area{id,name},created_at,updated_at"
    ),
    "calendar_entries": (
        "id,etag,summary,description,start_at,end_at,all_day,location,"
        "matter{id,display_number,description},calendar_owner{id,name},"
        "created_at,updated_at"
    ),
    "tasks": (
        "id,etag,name,status,priority,due_at,completed_at,description,"
        "assignee{id,name},matter{id,display_number,description},"
        "created_at,updated_at"
    ),
    "activities": (
        "id,etag,type,date,quantity,quantity_in_hours,price,total,note,"
        "flat_rate,billed,matter{id,display_number,description},"
        "user{id,name},created_at,updated_at"
    ),
    "notes": (
        "id,etag,type,subject,detail,date,author{id,name},"
        "matter{id,display_number},contact{id,name},created_at,updated_at"
    ),
    "documents": (
        "id,etag,name,content_type,size,locked,received_at,"
        "matter{id,display_number,description},"
        "document_category{id,name},"
        "latest_document_version{id,filename,size,content_type,fully_uploaded,put_url}"
    ),
    "users": "id,etag,name,first_name,last_name,email,enabled",
}

PATH_RESOURCE_FIELDS: dict[str, str] = {
    "users/who_am_i": DEFAULT_FIELDS["who_am_i"],
    "contacts": DEFAULT_FIELDS["contacts"],
    "matters": DEFAULT_FIELDS["matters"],
    "calendar_entries": DEFAULT_FIELDS["calendar_entries"],
    "tasks": DEFAULT_FIELDS["tasks"],
    "activities": DEFAULT_FIELDS["activities"],
    "notes": DEFAULT_FIELDS["notes"],
    "documents": DEFAULT_FIELDS["documents"],
    "users": DEFAULT_FIELDS["users"],
}

DOCUMENT_UPLOAD_GUIDANCE = (
    "Clio document upload is a 3-step process (v1 does not ship a binary upload tool):\n"
    "1) POST /documents via clio_api_request with body "
    '{"name": "file.pdf", "matter": {"id": MATTER_ID}} '
    "(auto-wrap is on). Response includes data.latest_document_version.put_url.\n"
    "2) HTTP PUT the raw file bytes to put_url (NOT through this MCP server).\n"
    "3) PATCH the document_version with fully_uploaded=true if Clio does not mark it automatically.\n"
    "Always clio_list_documents first so you do not create a duplicate name on the same matter."
)
