"""initial schema"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("routing_state", sa.String(length=64), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_status", "documents", ["status"])
    op.create_index("ix_documents_routing_state", "documents", ["routing_state"])

    op.create_table(
        "evaluation_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("document_type", sa.String(length=64), nullable=False),
        sa.Column("summary_json", sa.JSON(), nullable=False),
        sa.Column("report_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_evaluation_runs_name", "evaluation_runs", ["name"])
    op.create_index("ix_evaluation_runs_document_type", "evaluation_runs", ["document_type"])

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_jobs_document_id", "jobs", ["document_id"])
    op.create_index("ix_jobs_job_type", "jobs", ["job_type"])
    op.create_index("ix_jobs_status", "jobs", ["status"])

    op.create_table(
        "pages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("width", sa.Float(), nullable=False),
        sa.Column("height", sa.Float(), nullable=False),
        sa.Column("rotation", sa.Integer(), nullable=False),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_pages_document_id", "pages", ["document_id"])

    op.create_table(
        "engine_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("job_id", sa.String(length=36), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("engine_type", sa.String(length=64), nullable=False),
        sa.Column("engine_name", sa.String(length=255), nullable=False),
        sa.Column("engine_version", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("output_payload", sa.JSON(), nullable=False),
        sa.Column("metrics_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_engine_runs_document_id", "engine_runs", ["document_id"])
    op.create_index("ix_engine_runs_engine_type", "engine_runs", ["engine_type"])

    op.create_table(
        "parsed_regions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("pages.id"), nullable=False),
        sa.Column("region_type", sa.String(length=64), nullable=False),
        sa.Column("bbox_json", sa.JSON(), nullable=False),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_parsed_regions_document_id", "parsed_regions", ["document_id"])
    op.create_index("ix_parsed_regions_page_id", "parsed_regions", ["page_id"])
    op.create_index("ix_parsed_regions_region_type", "parsed_regions", ["region_type"])

    op.create_table(
        "ocr_spans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("page_id", sa.Integer(), sa.ForeignKey("pages.id"), nullable=False),
        sa.Column("span_type", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("bbox_json", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_engine", sa.String(length=255), nullable=False),
        sa.Column("reading_order", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_ocr_spans_document_id", "ocr_spans", ["document_id"])
    op.create_index("ix_ocr_spans_page_id", "ocr_spans", ["page_id"])

    op.create_table(
        "extracted_entities",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("schema_name", sa.String(length=128), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_extracted_entities_document_id", "extracted_entities", ["document_id"])

    op.create_table(
        "extracted_fields",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("entity_id", sa.Integer(), sa.ForeignKey("extracted_entities.id"), nullable=False),
        sa.Column("field_name", sa.String(length=128), nullable=False),
        sa.Column("value_text", sa.Text(), nullable=True),
        sa.Column("normalized_value", sa.JSON(), nullable=True),
        sa.Column("value_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("routing_state", sa.String(length=64), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_extracted_fields_entity_id", "extracted_fields", ["entity_id"])
    op.create_index("ix_extracted_fields_field_name", "extracted_fields", ["field_name"])
    op.create_index("ix_extracted_fields_routing_state", "extracted_fields", ["routing_state"])

    op.create_table(
        "field_evidence",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("field_id", sa.Integer(), sa.ForeignKey("extracted_fields.id"), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=False),
        sa.Column("bbox_json", sa.JSON(), nullable=True),
        sa.Column("evidence_text", sa.Text(), nullable=False),
        sa.Column("source_engine", sa.String(length=255), nullable=False),
        sa.Column("source_region_id", sa.String(length=255), nullable=True),
        sa.Column("grounding_score", sa.Float(), nullable=False),
    )
    op.create_index("ix_field_evidence_field_id", "field_evidence", ["field_id"])

    op.create_table(
        "validation_reports",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("field_id", sa.Integer(), sa.ForeignKey("extracted_fields.id"), nullable=True),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details_json", sa.JSON(), nullable=False),
    )
    op.create_index("ix_validation_reports_document_id", "validation_reports", ["document_id"])
    op.create_index("ix_validation_reports_field_id", "validation_reports", ["field_id"])
    op.create_index("ix_validation_reports_status", "validation_reports", ["status"])

    op.create_table(
        "review_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("document_id", sa.String(length=36), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("field_id", sa.Integer(), sa.ForeignKey("extracted_fields.id"), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("candidate_value", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_review_tasks_document_id", "review_tasks", ["document_id"])
    op.create_index("ix_review_tasks_field_id", "review_tasks", ["field_id"])
    op.create_index("ix_review_tasks_status", "review_tasks", ["status"])

    op.create_table(
        "review_decisions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("review_task_id", sa.Integer(), sa.ForeignKey("review_tasks.id"), nullable=False),
        sa.Column("decision", sa.String(length=32), nullable=False),
        sa.Column("final_value", sa.Text(), nullable=True),
        sa.Column("reviewer", sa.String(length=255), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_review_decisions_review_task_id", "review_decisions", ["review_task_id"])


def downgrade() -> None:
    op.drop_index("ix_review_decisions_review_task_id", table_name="review_decisions")
    op.drop_table("review_decisions")
    op.drop_index("ix_review_tasks_status", table_name="review_tasks")
    op.drop_index("ix_review_tasks_field_id", table_name="review_tasks")
    op.drop_index("ix_review_tasks_document_id", table_name="review_tasks")
    op.drop_table("review_tasks")
    op.drop_index("ix_validation_reports_status", table_name="validation_reports")
    op.drop_index("ix_validation_reports_field_id", table_name="validation_reports")
    op.drop_index("ix_validation_reports_document_id", table_name="validation_reports")
    op.drop_table("validation_reports")
    op.drop_index("ix_field_evidence_field_id", table_name="field_evidence")
    op.drop_table("field_evidence")
    op.drop_index("ix_extracted_fields_routing_state", table_name="extracted_fields")
    op.drop_index("ix_extracted_fields_field_name", table_name="extracted_fields")
    op.drop_index("ix_extracted_fields_entity_id", table_name="extracted_fields")
    op.drop_table("extracted_fields")
    op.drop_index("ix_extracted_entities_document_id", table_name="extracted_entities")
    op.drop_table("extracted_entities")
    op.drop_index("ix_ocr_spans_page_id", table_name="ocr_spans")
    op.drop_index("ix_ocr_spans_document_id", table_name="ocr_spans")
    op.drop_table("ocr_spans")
    op.drop_index("ix_parsed_regions_region_type", table_name="parsed_regions")
    op.drop_index("ix_parsed_regions_page_id", table_name="parsed_regions")
    op.drop_index("ix_parsed_regions_document_id", table_name="parsed_regions")
    op.drop_table("parsed_regions")
    op.drop_index("ix_engine_runs_engine_type", table_name="engine_runs")
    op.drop_index("ix_engine_runs_document_id", table_name="engine_runs")
    op.drop_table("engine_runs")
    op.drop_index("ix_pages_document_id", table_name="pages")
    op.drop_table("pages")
    op.drop_index("ix_jobs_status", table_name="jobs")
    op.drop_index("ix_jobs_job_type", table_name="jobs")
    op.drop_index("ix_jobs_document_id", table_name="jobs")
    op.drop_table("jobs")
    op.drop_index("ix_evaluation_runs_document_type", table_name="evaluation_runs")
    op.drop_index("ix_evaluation_runs_name", table_name="evaluation_runs")
    op.drop_table("evaluation_runs")
    op.drop_index("ix_documents_routing_state", table_name="documents")
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_table("documents")
