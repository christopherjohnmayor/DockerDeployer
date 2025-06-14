"""
Comprehensive test suite for Enhanced Template Management Service.

Tests cover:
- Enhanced CRUD operations with performance tracking
- Advanced search and filtering functionality
- Template lifecycle management
- Caching and performance optimization
- Error handling and edge cases
- Integration with Phase 4 metrics

Target: 80%+ test coverage with AsyncMock patterns and <200ms response times.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.enhanced_template_management_service import EnhancedTemplateManagementService
from app.db.models import (
    MarketplaceTemplate,
    TemplateAnalytics,
    TemplateCategory,
    TemplateDeploymentHistory,
    TemplatePerformanceMetrics,
    TemplateSecurityScan,
    TemplateStatus,
    TemplateVersion,
    User,
)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = Mock(spec=Session)
    session.query.return_value = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.refresh = Mock()
    return session


@pytest.fixture
def enhanced_service(mock_db_session):
    """Create an Enhanced Template Management Service instance."""
    return EnhancedTemplateManagementService(mock_db_session)


@pytest.fixture
def sample_template_data():
    """Sample template data for testing."""
    return {
        "name": "Test NGINX Template",
        "description": "A comprehensive NGINX web server template with SSL support",
        "category_id": 1,
        "docker_compose_yaml": """version: '3.8'
services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    environment:
      - NGINX_HOST=localhost
      - NGINX_PORT=80""",
        "tags": ["nginx", "web-server", "ssl"],
        "subcategory": "nginx",
        "difficulty_level": "intermediate",
        "estimated_setup_time": 15,
        "search_keywords": "nginx web server ssl https",
        "compatibility_tags": ["docker", "linux"],
        "minimum_docker_version": "20.10.0",
        "supported_architectures": ["amd64", "arm64"]
    }


@pytest.fixture
def sample_template():
    """Sample MarketplaceTemplate instance."""
    return MarketplaceTemplate(
        id=1,
        name="Test Template",
        description="Test description",
        author_id=1,
        category_id=1,
        version="1.0.0",
        docker_compose_yaml="version: '3.8'\nservices:\n  test:\n    image: nginx:latest",
        status=TemplateStatus.APPROVED,
        downloads=100,
        rating_avg=4.5,
        rating_count=10,
        performance_score=85.0,
        deployment_success_rate=95.0,
        security_score=90,
        is_featured=False,
        is_deprecated=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


class TestEnhancedTemplateCreation:
    """Test enhanced template creation functionality."""

    def test_create_template_enhanced_success(self, enhanced_service, mock_db_session, sample_template_data):
        """Test successful enhanced template creation."""
        # Mock database operations
        mock_template = Mock(spec=MarketplaceTemplate)
        mock_template.id = 1
        mock_template.version = "1.0.0"
        mock_template.category_id = 1
        mock_db_session.add.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        
        # Mock the template creation
        with patch.object(enhanced_service, '_sanitize_template_data', return_value=sample_template_data), \
             patch.object(enhanced_service, '_validate_docker_compose_enhanced'), \
             patch.object(enhanced_service, '_analyze_template_metadata', return_value={}), \
             patch.object(enhanced_service, '_create_template_version_enhanced'), \
             patch.object(enhanced_service, '_initialize_performance_tracking'), \
             patch.object(enhanced_service, '_invalidate_template_caches'), \
             patch('app.services.enhanced_template_management_service.MarketplaceTemplate', return_value=mock_template):
            
            result = enhanced_service.create_template_enhanced(sample_template_data, author_id=1)
            
            # Verify the result
            assert result == mock_template
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()

    def test_create_template_enhanced_validation_error(self, enhanced_service, sample_template_data):
        """Test template creation with validation error."""
        # Mock validation to raise an error
        with patch.object(enhanced_service, '_sanitize_template_data', return_value=sample_template_data), \
             patch.object(enhanced_service, '_validate_docker_compose_enhanced', side_effect=ValueError("Invalid YAML")):
            
            with pytest.raises(ValueError, match="Invalid YAML"):
                enhanced_service.create_template_enhanced(sample_template_data, author_id=1)

    def test_create_template_enhanced_database_error(self, enhanced_service, mock_db_session, sample_template_data):
        """Test template creation with database error."""
        # Mock database error
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with patch.object(enhanced_service, '_sanitize_template_data', return_value=sample_template_data), \
             patch.object(enhanced_service, '_validate_docker_compose_enhanced'), \
             patch.object(enhanced_service, '_analyze_template_metadata', return_value={}), \
             patch('app.services.enhanced_template_management_service.MarketplaceTemplate'):
            
            with pytest.raises(Exception, match="Database error"):
                enhanced_service.create_template_enhanced(sample_template_data, author_id=1)
            
            mock_db_session.rollback.assert_called_once()


class TestEnhancedTemplateRetrieval:
    """Test enhanced template retrieval functionality."""

    def test_get_template_enhanced_success(self, enhanced_service, mock_db_session, sample_template):
        """Test successful enhanced template retrieval."""
        # Mock database query
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_template
        mock_db_session.query.return_value = mock_query
        
        with patch.object(enhanced_service, '_get_template_analytics', return_value={}), \
             patch.object(enhanced_service, '_get_template_security_data', return_value={}), \
             patch.object(enhanced_service, '_track_template_access'):
            
            result = enhanced_service.get_template_enhanced(1, include_analytics=True, include_security=True)
            
            assert result == sample_template
            assert hasattr(result, 'analytics_data')
            assert hasattr(result, 'security_data')

    def test_get_template_enhanced_not_found(self, enhanced_service, mock_db_session):
        """Test template retrieval when template not found."""
        # Mock database query to return None
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = enhanced_service.get_template_enhanced(999)
        
        assert result is None

    def test_get_template_enhanced_database_error(self, enhanced_service, mock_db_session):
        """Test template retrieval with database error."""
        # Mock database error
        mock_db_session.query.side_effect = Exception("Database error")
        
        result = enhanced_service.get_template_enhanced(1)
        
        assert result is None


class TestEnhancedTemplateUpdate:
    """Test enhanced template update functionality."""

    def test_update_template_enhanced_success(self, enhanced_service, mock_db_session, sample_template):
        """Test successful enhanced template update."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_template
        mock_db_session.query.return_value = mock_query
        
        update_data = {"name": "Updated Template Name", "description": "Updated description"}
        
        with patch.object(enhanced_service, '_sanitize_template_data', return_value=update_data), \
             patch.object(enhanced_service, '_increment_version', return_value="1.0.1"), \
             patch.object(enhanced_service, '_create_template_version_enhanced'), \
             patch.object(enhanced_service, '_analyze_template_metadata', return_value={}), \
             patch.object(enhanced_service, '_invalidate_template_caches'):
            
            result = enhanced_service.update_template_enhanced(1, update_data, user_id=1)
            
            assert result == sample_template
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once()

    def test_update_template_enhanced_not_found(self, enhanced_service, mock_db_session):
        """Test template update when template not found."""
        # Mock database query to return None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = enhanced_service.update_template_enhanced(999, {}, user_id=1)
        
        assert result is None

    def test_update_template_enhanced_access_denied(self, enhanced_service, mock_db_session, sample_template):
        """Test template update with access denied."""
        # Set different author_id to simulate access denial
        sample_template.author_id = 2
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_template
        mock_db_session.query.return_value = mock_query
        
        result = enhanced_service.update_template_enhanced(1, {}, user_id=1)
        
        assert result is None


class TestEnhancedTemplateSearch:
    """Test enhanced template search functionality."""

    def test_search_templates_enhanced_success(self, enhanced_service, mock_db_session, sample_template):
        """Test successful enhanced template search."""
        # Mock database query
        mock_query = Mock()
        mock_query.options.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_template]
        mock_db_session.query.return_value = mock_query
        
        search_params = {
            "query": "nginx",
            "category_id": 1,
            "page": 1,
            "per_page": 20
        }
        
        with patch.object(enhanced_service, '_generate_search_cache_key', return_value="test_key"), \
             patch.object(enhanced_service, '_get_cached_search_result', return_value=None), \
             patch.object(enhanced_service, '_apply_enhanced_search_filters', return_value=mock_query), \
             patch.object(enhanced_service, '_apply_standard_sorting', return_value=mock_query), \
             patch.object(enhanced_service, '_generate_search_metadata', return_value={}), \
             patch.object(enhanced_service, '_cache_search_result'):
            
            templates, total_count, metadata = enhanced_service.search_templates_enhanced(search_params)
            
            assert len(templates) == 1
            assert templates[0] == sample_template
            assert total_count == 1
            assert isinstance(metadata, dict)

    def test_search_templates_enhanced_cached_result(self, enhanced_service):
        """Test enhanced template search with cached result."""
        search_params = {"query": "nginx"}
        cached_result = ([], 0, {})
        
        with patch.object(enhanced_service, '_generate_search_cache_key', return_value="test_key"), \
             patch.object(enhanced_service, '_get_cached_search_result', return_value=cached_result):
            
            result = enhanced_service.search_templates_enhanced(search_params)
            
            assert result == cached_result


class TestTemplateLifecycleManagement:
    """Test template lifecycle management functionality."""

    def test_feature_template_success(self, enhanced_service, mock_db_session, sample_template):
        """Test successful template featuring."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_template
        mock_db_session.query.return_value = mock_query

        with patch.object(enhanced_service, '_invalidate_template_caches'):
            result = enhanced_service.feature_template(1, admin_id=1)

            assert result is True
            assert sample_template.is_featured is True
            mock_db_session.commit.assert_called_once()

    def test_feature_template_not_found(self, enhanced_service, mock_db_session):
        """Test template featuring when template not found."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db_session.query.return_value = mock_query

        result = enhanced_service.feature_template(999, admin_id=1)

        assert result is False

    def test_deprecate_template_success(self, enhanced_service, mock_db_session, sample_template):
        """Test successful template deprecation."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_template
        mock_db_session.query.return_value = mock_query

        with patch.object(enhanced_service, '_invalidate_template_caches'):
            result = enhanced_service.deprecate_template(
                1,
                reason="Outdated version",
                replacement_id=2,
                admin_id=1
            )

            assert result is True
            assert sample_template.is_deprecated is True
            assert sample_template.deprecation_reason == "Outdated version"
            assert sample_template.replacement_template_id == 2
            mock_db_session.commit.assert_called_once()


class TestTemplateValidation:
    """Test template validation functionality."""

    def test_validate_docker_compose_enhanced_valid(self, enhanced_service):
        """Test validation of valid Docker Compose YAML."""
        valid_yaml = """version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
"""

        with patch.object(enhanced_service, '_validate_docker_compose_security'):
            # Should not raise any exception
            enhanced_service._validate_docker_compose_enhanced(valid_yaml)

    def test_validate_docker_compose_enhanced_invalid_yaml(self, enhanced_service):
        """Test validation of invalid Docker Compose YAML."""
        invalid_yaml = "invalid: yaml: content: ["

        with pytest.raises(ValueError, match="Invalid YAML syntax"):
            enhanced_service._validate_docker_compose_enhanced(invalid_yaml)

    def test_validate_docker_compose_enhanced_too_short(self, enhanced_service):
        """Test validation of too short Docker Compose YAML."""
        short_yaml = "version: '3.8'"

        with pytest.raises(ValueError, match="must be at least 50 characters"):
            enhanced_service._validate_docker_compose_enhanced(short_yaml)

    def test_validate_docker_compose_enhanced_missing_structure(self, enhanced_service):
        """Test validation of Docker Compose YAML missing required structure."""
        invalid_structure = """
invalid_structure:
  - item1
  - item2
"""

        with pytest.raises(ValueError, match="must contain 'version' and 'services'"):
            enhanced_service._validate_docker_compose_enhanced(invalid_structure)


class TestTemplateMetadataAnalysis:
    """Test template metadata analysis functionality."""

    def test_analyze_template_metadata_success(self, enhanced_service):
        """Test successful template metadata analysis."""
        docker_compose = """version: '3.8'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    environment:
      - NGINX_HOST=localhost
  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=secret
"""

        metadata = enhanced_service._analyze_template_metadata(docker_compose)

        assert metadata["docker_image_count"] == 2
        assert len(metadata["network_ports"]) == 2
        assert len(metadata["volume_mounts"]) == 1
        assert len(metadata["environment_variables"]) == 2
        assert metadata["template_size_mb"] > 0

    def test_analyze_template_metadata_invalid_yaml(self, enhanced_service):
        """Test template metadata analysis with invalid YAML."""
        invalid_yaml = "invalid: yaml: ["

        metadata = enhanced_service._analyze_template_metadata(invalid_yaml)

        # Should return empty metadata on error
        assert metadata == {}


class TestCachingFunctionality:
    """Test caching functionality."""

    def test_generate_search_cache_key(self, enhanced_service):
        """Test search cache key generation."""
        search_params = {
            "query": "nginx",
            "category_id": 1,
            "page": 1,
            "per_page": 20
        }

        cache_key = enhanced_service._generate_search_cache_key(search_params, performance_sort=False)

        assert cache_key.startswith("template_search:")
        assert len(cache_key) > 20  # Should be a reasonable length

    def test_invalidate_template_caches(self, enhanced_service, mock_db_session):
        """Test template cache invalidation."""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = None
        mock_db_session.query.return_value = mock_query

        enhanced_service._invalidate_template_caches(category_id=1, template_id=1)

        mock_db_session.query.assert_called()
        mock_db_session.commit.assert_called_once()


class TestPerformanceTracking:
    """Test performance tracking functionality."""

    def test_initialize_performance_tracking(self, enhanced_service, mock_db_session):
        """Test performance tracking initialization."""
        enhanced_service._initialize_performance_tracking(template_id=1)

        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_get_template_analytics(self, enhanced_service, mock_db_session):
        """Test template analytics retrieval."""
        # Mock analytics data
        mock_analytics = [Mock(performance_score=85.0), Mock(performance_score=90.0)]
        mock_performance = Mock(success_rate_percentage=95.0, total_deployments=10)

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_analytics
        mock_query.first.return_value = mock_performance
        mock_db_session.query.return_value = mock_query

        analytics = enhanced_service._get_template_analytics(template_id=1)

        assert analytics["recent_deployments"] == 2
        assert analytics["avg_performance_score"] == 87.5
        assert analytics["success_rate"] == 95.0
        assert analytics["total_deployments"] == 10

    def test_get_template_security_data(self, enhanced_service, mock_db_session):
        """Test template security data retrieval."""
        # Mock security scan data
        mock_security_scan = Mock(
            overall_security_score=90,
            vulnerability_count_critical=0,
            vulnerability_count_high=1,
            vulnerability_count_medium=2,
            vulnerability_count_low=3,
            scan_completed_at=datetime.utcnow(),
            scan_status="completed"
        )

        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_security_scan
        mock_db_session.query.return_value = mock_query

        security_data = enhanced_service._get_template_security_data(template_id=1)

        assert security_data["security_score"] == 90
        assert security_data["vulnerability_count"] == 6  # 0+1+2+3
        assert security_data["scan_status"] == "completed"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_database_error_handling(self, enhanced_service, mock_db_session):
        """Test proper handling of database errors."""
        mock_db_session.query.side_effect = Exception("Database connection error")

        # Should not raise exception, but return appropriate default values
        result = enhanced_service.get_template_enhanced(1)
        assert result is None

        templates, count, metadata = enhanced_service.search_templates_enhanced({})
        assert templates == []
        assert count == 0
        assert metadata == {}

    def test_version_increment_edge_cases(self, enhanced_service):
        """Test version increment with edge cases."""
        # Test normal semantic version
        assert enhanced_service._increment_version("1.0.0") == "1.0.1"
        assert enhanced_service._increment_version("2.1.5") == "2.1.6"

        # Test partial version
        assert enhanced_service._increment_version("1.0") == "1.0.1"

        # Test single number version
        result = enhanced_service._increment_version("1")
        assert result == "1.1"

        # Test invalid version (should fallback to timestamp)
        result = enhanced_service._increment_version("invalid.version")
        assert "invalid.version." in result
