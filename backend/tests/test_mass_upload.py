"""
Tests for mass upload processor functionality.
"""

import json
from datetime import datetime

import pytest

from app.scrapers.mass_upload import (
    CSVUploadProcessor,
    JSONUploadProcessor,
    MassUploadProcessor,
    FieldMappingValidator,
    DEFAULT_FIELD_MAPPINGS,
)
from app.scrapers.base import JobPosting


class TestFieldMappingValidator:
    """Test field mapping validation"""

    def test_valid_mapping(self):
        """Test valid field mapping creation"""
        mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
        }
        validator = FieldMappingValidator(mapping)
        assert validator.field_mapping == mapping

    def test_invalid_target_field(self):
        """Test that invalid target fields are rejected"""
        mapping = {
            "Job Title": "title",
            "Description": "invalid_field",
        }
        with pytest.raises(ValueError, match="Invalid target fields"):
            FieldMappingValidator(mapping)

    def test_required_fields_check(self):
        """Test checking for required fields"""
        incomplete_mapping = {
            "Job Title": "title",
            "Description": "description",
            # Missing company
        }
        validator = FieldMappingValidator(incomplete_mapping)
        assert not validator.has_required_fields()

        complete_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
        }
        validator2 = FieldMappingValidator(complete_mapping)
        assert validator2.has_required_fields()

    def test_apply_mapping_success(self):
        """Test successful field mapping"""
        mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
            "Location": "location",
        }
        validator = FieldMappingValidator(mapping)

        row = {
            "Job Title": "Software Engineer",
            "Description": "Build great software",
            "Company": "TechCorp",
            "Location": "San Francisco, CA",
        }

        mapped, errors = validator.apply(row)

        assert errors == []
        assert mapped["title"] == "Software Engineer"
        assert mapped["description"] == "Build great software"
        assert mapped["company"] == "TechCorp"
        assert mapped["location"] == "San Francisco, CA"

    def test_apply_mapping_missing_required(self):
        """Test mapping with missing required field"""
        mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
        }
        validator = FieldMappingValidator(mapping)

        row = {
            "Job Title": "Engineer",
            "Description": "Build software",
            # Missing company
        }

        mapped, errors = validator.apply(row)

        assert len(errors) > 0
        assert any("company" in e.lower() for e in errors)

    def test_salary_conversion(self):
        """Test salary field type conversion"""
        mapping = {
            "Title": "title",
            "Description": "description",
            "Company": "company",
            "Min Salary": "salary_min",
            "Max Salary": "salary_max",
        }
        validator = FieldMappingValidator(mapping)

        row = {
            "Title": "Engineer",
            "Description": "Build software",
            "Company": "TechCorp",
            "Min Salary": "100000",
            "Max Salary": "150000",
        }

        mapped, errors = validator.apply(row)

        assert errors == []
        assert mapped["salary_min"] == 100000
        assert mapped["salary_max"] == 150000
        assert isinstance(mapped["salary_min"], int)
        assert isinstance(mapped["salary_max"], int)

    def test_invalid_salary(self):
        """Test invalid salary value"""
        mapping = {
            "Title": "title",
            "Description": "description",
            "Company": "company",
            "Salary": "salary_max",
        }
        validator = FieldMappingValidator(mapping)

        row = {
            "Title": "Engineer",
            "Description": "Build software",
            "Company": "TechCorp",
            "Salary": "not_a_number",
        }

        mapped, errors = validator.apply(row)

        assert len(errors) > 0
        assert any("Invalid value" in e for e in errors)


class TestCSVUploadProcessor:
    """Test CSV file processing"""

    @pytest.mark.asyncio
    async def test_simple_csv_parsing(self):
        """Test basic CSV parsing"""
        csv_content = """Job Title,Description,Company,Location
Software Engineer,Build great software,TechCorp,San Francisco
Data Scientist,Analyze data,DataCo,New York
Product Manager,Manage products,ProductCo,Austin"""

        field_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
            "Location": "location",
        }

        processor = CSVUploadProcessor(field_mapping)
        jobs = []

        async for job, errors in processor.process_file(csv_content):
            if job:
                jobs.append(job)
            assert not errors

        assert len(jobs) == 3
        assert jobs[0].title == "Software Engineer"
        assert jobs[1].company == "DataCo"
        assert jobs[2].location == "Austin"

    @pytest.mark.asyncio
    async def test_csv_with_missing_column(self):
        """Test CSV with missing required column"""
        csv_content = """Job Title,Description
Software Engineer,Build great software"""

        field_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",  # This column doesn't exist in CSV
        }

        processor = CSVUploadProcessor(field_mapping)
        has_error = False

        async for job, errors in processor.process_file(csv_content):
            if errors:
                has_error = True
                assert any("Missing CSV columns" in e for e in errors)

        assert has_error

    @pytest.mark.asyncio
    async def test_csv_empty_file(self):
        """Test empty CSV file"""
        csv_content = ""

        field_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
        }

        processor = CSVUploadProcessor(field_mapping)
        has_error = False

        async for job, errors in processor.process_file(csv_content):
            if errors:
                has_error = True
                assert "CSV file is empty" in errors[0]

        assert has_error

    @pytest.mark.asyncio
    async def test_csv_with_delimiter(self):
        """Test CSV with custom delimiter"""
        csv_content = """Job Title|Description|Company|Location
Software Engineer|Build software|TechCorp|SF
Data Scientist|Analyze data|DataCo|NY"""

        field_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
            "Location": "location",
        }

        processor = CSVUploadProcessor(field_mapping)
        jobs = []

        async for job, errors in processor.process_file(csv_content, delimiter="|"):
            if job:
                jobs.append(job)

        assert len(jobs) == 2
        assert jobs[0].title == "Software Engineer"


class TestJSONUploadProcessor:
    """Test JSON file processing"""

    @pytest.mark.asyncio
    async def test_json_array(self):
        """Test JSON array format"""
        json_data = json.dumps([
            {
                "title": "Software Engineer",
                "description": "Build great software",
                "company": "TechCorp",
                "location": "San Francisco",
            },
            {
                "title": "Data Scientist",
                "description": "Analyze data",
                "company": "DataCo",
                "location": "New York",
            },
        ])

        processor = JSONUploadProcessor()
        jobs = []

        async for job, errors in processor.process_file(json_data):
            if job:
                jobs.append(job)
            assert not errors

        assert len(jobs) == 2
        assert jobs[0].title == "Software Engineer"
        assert jobs[1].company == "DataCo"

    @pytest.mark.asyncio
    async def test_json_single_object(self):
        """Test JSON single object format"""
        json_data = json.dumps({
            "title": "Software Engineer",
            "description": "Build great software",
            "company": "TechCorp",
            "location": "San Francisco",
        })

        processor = JSONUploadProcessor()
        jobs = []

        async for job, errors in processor.process_file(json_data):
            if job:
                jobs.append(job)
            assert not errors

        assert len(jobs) == 1
        assert jobs[0].title == "Software Engineer"

    @pytest.mark.asyncio
    async def test_json_missing_required_field(self):
        """Test JSON with missing required field"""
        json_data = json.dumps([
            {
                "title": "Engineer",
                "description": "Build software",
                # Missing company
            },
        ])

        processor = JSONUploadProcessor()
        has_error = False

        async for job, errors in processor.process_file(json_data):
            if errors:
                has_error = True
                assert any("required field" in e.lower() for e in errors)

        assert has_error

    @pytest.mark.asyncio
    async def test_json_invalid_format(self):
        """Test invalid JSON format"""
        json_data = "{ invalid json }"

        processor = JSONUploadProcessor()
        has_error = False

        async for job, errors in processor.process_file(json_data):
            if errors:
                has_error = True
                assert any("Invalid JSON" in e for e in errors)

        assert has_error

    @pytest.mark.asyncio
    async def test_json_with_optional_fields(self):
        """Test JSON with optional fields"""
        json_data = json.dumps({
            "title": "Engineer",
            "description": "Build software",
            "company": "TechCorp",
            "salary_min": 100000,
            "salary_max": 150000,
            "posted_date": "2026-06-01T10:00:00Z",
        })

        processor = JSONUploadProcessor()
        jobs = []

        async for job, errors in processor.process_file(json_data):
            if job:
                jobs.append(job)
            assert not errors

        assert len(jobs) == 1
        job = jobs[0]
        assert job.salary_min == 100000
        assert job.salary_max == 150000
        assert job.posted_date is not None


class TestMassUploadProcessor:
    """Test the main orchestration processor"""

    @pytest.mark.asyncio
    async def test_csv_upload(self):
        """Test CSV upload processing"""
        from app.models.job_scraping import UploadType

        csv_content = """Job Title,Description,Company
Engineer,Build software,TechCorp
Designer,Design UI,DesignCo"""

        field_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
        }

        processor = MassUploadProcessor()
        jobs = []

        async for job, errors in processor.process_upload(
            UploadType.csv, csv_content, field_mapping
        ):
            if job:
                jobs.append(job)

        assert len(jobs) == 2
        assert jobs[0].title == "Engineer"
        assert jobs[0].source == "csv_upload"

    @pytest.mark.asyncio
    async def test_json_upload(self):
        """Test JSON upload processing"""
        from app.models.job_scraping import UploadType

        json_content = json.dumps([
            {"title": "Engineer", "description": "Build software", "company": "TechCorp"},
            {"title": "Designer", "description": "Design UI", "company": "DesignCo"},
        ])

        processor = MassUploadProcessor()
        jobs = []

        async for job, errors in processor.process_upload(
            UploadType.json, json_content
        ):
            if job:
                jobs.append(job)

        assert len(jobs) == 2
        assert jobs[0].title == "Engineer"
        assert jobs[0].source == "json_upload"

    @pytest.mark.asyncio
    async def test_upload_bytes_conversion(self):
        """Test that bytes are properly converted to string"""
        from app.models.job_scraping import UploadType

        csv_content = b"""Job Title,Description,Company
Engineer,Build software,TechCorp"""

        field_mapping = {
            "Job Title": "title",
            "Description": "description",
            "Company": "company",
        }

        processor = MassUploadProcessor()
        jobs = []

        async for job, errors in processor.process_upload(
            UploadType.csv, csv_content, field_mapping
        ):
            if job:
                jobs.append(job)

        assert len(jobs) == 1


class TestDefaultMappings:
    """Test pre-configured field mappings"""

    def test_linkedin_mapping_exists(self):
        """Test that LinkedIn mapping is available"""
        assert "linkedin_export" in DEFAULT_FIELD_MAPPINGS
        mapping = DEFAULT_FIELD_MAPPINGS["linkedin_export"]
        assert "Job Title" in mapping
        assert mapping["Job Title"] == "title"

    def test_ziprecruiter_mapping_exists(self):
        """Test that ZipRecruiter mapping is available"""
        assert "ziprecruiter_export" in DEFAULT_FIELD_MAPPINGS

    def test_generic_mapping_complete(self):
        """Test that generic mapping has all standard fields"""
        mapping = DEFAULT_FIELD_MAPPINGS["generic_job_board"]
        required_fields = {"title", "description", "company"}

        mapped_fields = set(mapping.values())
        assert required_fields.issubset(mapped_fields)
