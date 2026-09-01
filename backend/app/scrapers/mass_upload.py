"""
Mass upload processor for CSV and JSON job imports.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from typing import AsyncGenerator

from app.scrapers.base import JobPosting
from app.models.job_scraping import UploadType


class FieldMappingValidator:
    """Validates and applies field mappings to uploaded data"""

    STANDARD_FIELDS = {
        "title",
        "description",
        "company",
        "location",
        "job_type",
        "salary_min",
        "salary_max",
        "posted_date",
        "external_url",
        "external_id",
    }

    REQUIRED_FIELDS = {"title", "description", "company"}

    def __init__(self, field_mapping: dict):
        """
        Initialize with field mapping.

        Args:
            field_mapping: Dict mapping source columns to job fields
            Example: {"Job Title": "title", "Description": "description", ...}
        """
        self.field_mapping = field_mapping
        self.validate()

    def validate(self) -> None:
        """Validate that all target fields are valid"""
        invalid_fields = set(self.field_mapping.values()) - self.STANDARD_FIELDS
        if invalid_fields:
            raise ValueError(
                f"Invalid target fields: {invalid_fields}. "
                f"Must be one of: {self.STANDARD_FIELDS}"
            )

    def has_required_fields(self) -> bool:
        """Check if mapping covers all required fields"""
        mapped_fields = set(self.field_mapping.values())
        return self.REQUIRED_FIELDS.issubset(mapped_fields)

    def apply(self, row: dict) -> tuple[dict, list[str]]:
        """
        Apply mapping to a single row.

        Args:
            row: Dict with source column names as keys

        Returns:
            (mapped_dict, list_of_errors)
            mapped_dict has standardized field names and validated values
            list_of_errors contains validation errors
        """
        mapped = {}
        errors = []

        for source_col, target_field in self.field_mapping.items():
            if source_col not in row:
                # Source column missing
                if target_field in self.REQUIRED_FIELDS:
                    errors.append(f"Required field '{target_field}' not found in source column '{source_col}'")
                continue

            value = row[source_col]

            # Type conversion based on target field
            try:
                if target_field in {"salary_min", "salary_max"}:
                    mapped[target_field] = int(value) if value else None
                elif target_field == "posted_date":
                    # Try parsing ISO format
                    if value:
                        mapped[target_field] = datetime.fromisoformat(value.replace("Z", "+00:00"))
                elif target_field in {"title", "description", "company", "location", "job_type"}:
                    mapped[target_field] = str(value).strip() if value else None
                else:
                    mapped[target_field] = value
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid value for '{target_field}': {str(e)}")

        return mapped, errors


class CSVUploadProcessor:
    """Process CSV file uploads for bulk job import"""

    def __init__(self, field_mapping: dict):
        """
        Initialize CSV processor.

        Args:
            field_mapping: Dict mapping CSV columns to job fields
        """
        self.validator = FieldMappingValidator(field_mapping)

    async def process_file(
        self, file_content: str, delimiter: str = ","
    ) -> AsyncGenerator[tuple[JobPosting | None, list[str]], None]:
        """
        Process CSV file content and yield job postings.

        Args:
            file_content: CSV file content as string
            delimiter: CSV delimiter (default comma)

        Yields:
            (JobPosting or None, list_of_errors)
        """
        reader = csv.DictReader(StringIO(file_content), delimiter=delimiter)

        if not reader.fieldnames:
            yield None, ["CSV file is empty"]
            return

        # Verify source columns exist
        source_cols = set(self.validator.field_mapping.keys())
        csv_cols = set(reader.fieldnames)
        missing_cols = source_cols - csv_cols
        if missing_cols:
            yield None, [f"Missing CSV columns: {missing_cols}"]
            return

        for row in reader:
            mapped, errors = self.validator.apply(row)

            if errors:
                yield None, errors
                continue

            # Check required fields
            if not all(mapped.get(f) for f in {"title", "description", "company"}):
                yield None, ["Missing required fields: title, description, company"]
                continue

            job = JobPosting(
                title=mapped["title"],
                description=mapped["description"],
                company=mapped["company"],
                location=mapped.get("location"),
                job_type=mapped.get("job_type"),
                salary_min=mapped.get("salary_min"),
                salary_max=mapped.get("salary_max"),
                posted_date=mapped.get("posted_date"),
                external_url=mapped.get("external_url"),
                external_id=mapped.get("external_id"),
                source="csv_upload",
            )

            yield job, []


class JSONUploadProcessor:
    """Process JSON file uploads for bulk job import"""

    def __init__(self):
        """Initialize JSON processor (no field mapping needed)"""
        pass

    async def process_file(
        self, file_content: str
    ) -> AsyncGenerator[tuple[JobPosting | None, list[str]], None]:
        """
        Process JSON file content and yield job postings.

        Accepts either:
        - Array of job objects: [{"title": "...", "description": "...", ...}]
        - Single job object: {"title": "...", "description": "...", ...}

        Args:
            file_content: JSON file content as string

        Yields:
            (JobPosting or None, list_of_errors)
        """
        try:
            data = json.loads(file_content)
        except json.JSONDecodeError as e:
            yield None, [f"Invalid JSON: {str(e)}"]
            return

        # Normalize to list
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            yield None, ["JSON must be an object or array of objects"]
            return

        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                yield None, [f"Item {idx} is not a JSON object"]
                continue

            errors = []

            # Validate required fields
            for required_field in {"title", "description", "company"}:
                if required_field not in item or not item[required_field]:
                    errors.append(f"Missing required field: {required_field}")

            if errors:
                yield None, errors
                continue

            # Type conversion
            try:
                job = JobPosting(
                    title=str(item.get("title", "")).strip(),
                    description=str(item.get("description", "")).strip(),
                    company=str(item.get("company", "")).strip(),
                    location=str(item.get("location", "")).strip() if item.get("location") else None,
                    job_type=str(item.get("job_type", "")).strip() if item.get("job_type") else None,
                    salary_min=int(item["salary_min"]) if "salary_min" in item and item["salary_min"] else None,
                    salary_max=int(item["salary_max"]) if "salary_max" in item and item["salary_max"] else None,
                    posted_date=(
                        datetime.fromisoformat(item["posted_date"].replace("Z", "+00:00"))
                        if "posted_date" in item and item["posted_date"]
                        else None
                    ),
                    external_url=item.get("external_url"),
                    external_id=item.get("external_id"),
                    source="json_upload",
                )

                yield job, []

            except (ValueError, TypeError) as e:
                yield None, [f"Invalid data type: {str(e)}"]


class MassUploadProcessor:
    """Orchestrate processing of mass uploads"""

    def __init__(self):
        self.csv_processor = None
        self.json_processor = None

    def get_processor(self, upload_type: UploadType, field_mapping: dict | None = None):
        """Get appropriate processor for upload type"""
        if upload_type == UploadType.csv:
            if not field_mapping:
                raise ValueError("field_mapping required for CSV uploads")
            return CSVUploadProcessor(field_mapping)
        elif upload_type == UploadType.json:
            return JSONUploadProcessor()
        else:
            raise ValueError(f"Unknown upload type: {upload_type}")

    async def process_upload(
        self,
        upload_type: UploadType,
        file_content: str | bytes,
        field_mapping: dict | None = None,
    ) -> AsyncGenerator[tuple[JobPosting | None, list[str]], None]:
        """
        Process a file upload and yield parsed jobs.

        Args:
            upload_type: Type of upload (csv, json)
            file_content: File content (string for text, bytes for binary)
            field_mapping: Field mapping (required for CSV)

        Yields:
            (JobPosting or None, list_of_errors)
        """
        # Convert bytes to string if needed
        if isinstance(file_content, bytes):
            file_content = file_content.decode("utf-8")

        processor = self.get_processor(upload_type, field_mapping)

        async for job, errors in processor.process_file(file_content):
            yield job, errors


# Pre-configured field mappings for common sources
DEFAULT_FIELD_MAPPINGS = {
    "linkedin_export": {
        "Job Title": "title",
        "Job Description": "description",
        "Company": "company",
        "Location": "location",
        "Job Type": "job_type",
        "Job URL": "external_url",
    },
    "ziprecruiter_export": {
        "Job Title": "title",
        "Job Description": "description",
        "Company Name": "company",
        "Job Location": "location",
        "Salary": "salary_max",  # ZR doesn't separate min/max
        "Job URL": "external_url",
    },
    "indeed_export": {
        "Job Title": "title",
        "Description": "description",
        "Company": "company",
        "Location": "location",
        "Job ID": "external_id",
    },
    "generic_job_board": {
        "Title": "title",
        "Description": "description",
        "Company": "company",
        "Location": "location",
        "Type": "job_type",
        "Min Salary": "salary_min",
        "Max Salary": "salary_max",
        "Posted": "posted_date",
        "URL": "external_url",
        "ID": "external_id",
    },
}
