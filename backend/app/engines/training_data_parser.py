"""
Training Data Parser - Process CSV/JSON uploads for training system.

Handles:
- CSV and JSON file parsing
- Data validation
- Candidate profile extraction
- Error handling and reporting
"""
import csv
import json
import logging
from io import StringIO
from typing import Any

logger = logging.getLogger(__name__)


class TrainingDataValidationError(Exception):
    """Raised when training data validation fails."""
    pass


class TrainingDataParser:
    """Parse CSV/JSON training data files."""

    REQUIRED_FIELDS = {"candidate_name", "decision", "reasoning"}
    OPTIONAL_FIELDS = {"candidate_email", "rating", "skills", "experience_years", "education"}
    VALID_DECISIONS = {"hire", "reject", "applied", "interested", "not_interested"}

    @staticmethod
    async def parse_file(
        file_content: bytes,
        filename: str,
        file_format: str,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """
        Parse training data file (CSV or JSON).

        Args:
            file_content: Raw file bytes
            filename: Original filename
            file_format: 'csv' or 'json'

        Returns:
            Tuple of (parsed_items, error_messages)
            - parsed_items: List of validated candidate records
            - error_messages: List of validation errors encountered
        """
        errors = []
        items = []

        try:
            if file_format == "csv":
                items, csv_errors = await TrainingDataParser._parse_csv(file_content)
                errors.extend(csv_errors)
            elif file_format == "json":
                items, json_errors = await TrainingDataParser._parse_json(file_content)
                errors.extend(json_errors)
            else:
                raise TrainingDataValidationError(f"Unsupported format: {file_format}")

            # Validate each item
            validated_items = []
            for i, item in enumerate(items, 1):
                try:
                    validated = TrainingDataParser._validate_item(item, row_number=i)
                    validated_items.append(validated)
                except TrainingDataValidationError as e:
                    errors.append(f"Row {i}: {str(e)}")

            logger.info(
                "Parsed training data file",
                extra={
                    "uploaded_filename": filename,
                    "format": file_format,
                    "total_rows": len(items),
                    "valid_rows": len(validated_items),
                    "errors": len(errors),
                },
            )

            return validated_items, errors

        except Exception as e:
            logger.error(
                "Error parsing training data file",
                extra={"uploaded_filename": filename, "error": str(e)},
            )
            raise TrainingDataValidationError(f"Failed to parse file: {str(e)}")

    @staticmethod
    async def _parse_csv(file_content: bytes) -> tuple[list[dict], list[str]]:
        """Parse CSV file."""
        errors = []
        items = []

        try:
            # Decode bytes to string
            text = file_content.decode("utf-8")
            reader = csv.DictReader(StringIO(text))

            if not reader.fieldnames:
                raise TrainingDataValidationError("CSV file is empty")

            # Check for required fields
            missing_fields = TrainingDataParser.REQUIRED_FIELDS - set(reader.fieldnames)
            if missing_fields:
                raise TrainingDataValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}"
                )

            for row in reader:
                # Skip empty rows
                if not any(row.values()):
                    continue

                # Clean up None values
                item = {k: v.strip() if isinstance(v, str) else v for k, v in row.items() if v}
                items.append(item)

            return items, errors

        except Exception as e:
            errors.append(f"CSV parsing error: {str(e)}")
            return items, errors

    @staticmethod
    async def _parse_json(file_content: bytes) -> tuple[list[dict], list[str]]:
        """Parse JSON file."""
        errors = []
        items = []

        try:
            text = file_content.decode("utf-8")
            data = json.loads(text)

            if not isinstance(data, list):
                raise TrainingDataValidationError("JSON must be an array of objects")

            items = data
            return items, errors

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
            return items, errors
        except Exception as e:
            errors.append(f"JSON parsing error: {str(e)}")
            return items, errors

    @staticmethod
    def _validate_item(item: dict[str, Any], row_number: int = 0) -> dict[str, Any]:
        """Validate and normalize a single training data item."""
        # Check required fields
        for field in TrainingDataParser.REQUIRED_FIELDS:
            if field not in item or not str(item.get(field, "")).strip():
                raise TrainingDataValidationError(f"Missing or empty required field: {field}")

        # Validate decision
        decision = str(item.get("decision", "")).strip().lower()
        if decision not in TrainingDataParser.VALID_DECISIONS:
            raise TrainingDataValidationError(
                f"Invalid decision '{decision}'. Must be one of: {', '.join(TrainingDataParser.VALID_DECISIONS)}"
            )

        # Validate rating if present
        rating = item.get("rating")
        if rating is not None:
            try:
                rating_int = int(rating)
                if not 1 <= rating_int <= 5:
                    raise ValueError("Rating must be between 1 and 5")
                item["rating"] = rating_int
            except (ValueError, TypeError):
                raise TrainingDataValidationError(f"Invalid rating: {rating}")

        # Parse skills if present
        skills = item.get("skills", "")
        if skills:
            if isinstance(skills, str):
                item["skills"] = [s.strip() for s in skills.split(",") if s.strip()]
            elif isinstance(skills, list):
                item["skills"] = [str(s).strip() for s in skills if s]

        # Parse experience if present
        experience = item.get("experience_years")
        if experience is not None:
            try:
                item["experience_years"] = int(experience)
            except (ValueError, TypeError):
                pass  # Keep as-is if not a valid number

        # Normalize field names and remove unknown fields
        normalized = {
            "candidate_name": str(item.get("candidate_name", "")).strip(),
            "candidate_email": str(item.get("candidate_email", "")).strip(),
            "decision": decision,
            "reasoning": str(item.get("reasoning", "")).strip(),
            "rating": item.get("rating"),
            "skills": item.get("skills", []),
            "experience_years": item.get("experience_years"),
            "education": str(item.get("education", "")).strip(),
            "source_row": row_number,
        }

        return normalized
