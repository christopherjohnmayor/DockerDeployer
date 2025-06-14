"""
Enhanced Template Management Service for Phase 5 Template Marketplace.

This service provides comprehensive template management functionality including:
- Advanced CRUD operations with performance tracking
- Enhanced search and filtering with caching
- Template lifecycle management and versioning
- Performance analytics integration with Phase 4 metrics
- Security validation and approval workflow
- Comprehensive error handling and monitoring

Integrates with existing authentication and RBAC system.
Target: 80%+ test coverage with AsyncMock patterns and <200ms API response times.
"""

import html
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import uuid4

from sqlalchemy import and_, desc, func, or_, text
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import (
    MarketplaceTemplate,
    TemplateAnalytics,
    TemplateCategory,
    TemplateDeploymentHistory,
    TemplateMarketplaceCache,
    TemplatePerformanceMetrics,
    TemplateReview,
    TemplateSecurityScan,
    TemplateStatus,
    TemplateVersion,
    User,
)

logger = logging.getLogger(__name__)


class EnhancedTemplateManagementService:
    """Enhanced service class for comprehensive template marketplace operations."""

    def __init__(self, db: Session):
        """Initialize the service with database session."""
        self.db = db
        self.cache_ttl = 3600  # 1 hour default cache TTL

    # ===== ENHANCED CRUD OPERATIONS =====

    def create_template_enhanced(
        self, 
        template_data: Dict[str, Any], 
        author_id: int,
        auto_analyze: bool = True
    ) -> MarketplaceTemplate:
        """
        Create a new marketplace template with enhanced metadata and analytics.
        
        Args:
            template_data: Template creation data with enhanced fields
            author_id: ID of the template author
            auto_analyze: Whether to automatically analyze template metadata
            
        Returns:
            Created MarketplaceTemplate instance
            
        Raises:
            ValueError: If template data is invalid
            SQLAlchemyError: If database operation fails
        """
        try:
            # Sanitize and validate input data
            sanitized_data = self._sanitize_template_data(template_data)
            self._validate_docker_compose_enhanced(sanitized_data["docker_compose_yaml"])
            
            # Analyze template metadata if requested
            if auto_analyze:
                metadata = self._analyze_template_metadata(sanitized_data["docker_compose_yaml"])
                sanitized_data.update(metadata)
            
            # Create enhanced template
            template = MarketplaceTemplate(
                # Basic fields
                name=sanitized_data["name"],
                description=sanitized_data["description"],
                author_id=author_id,
                category_id=sanitized_data["category_id"],
                version=sanitized_data.get("version", "1.0.0"),
                docker_compose_yaml=sanitized_data["docker_compose_yaml"],
                tags=sanitized_data.get("tags", []),
                status=TemplateStatus.PENDING,
                
                # Enhanced metadata (Phase 5)
                subcategory=sanitized_data.get("subcategory"),
                difficulty_level=sanitized_data.get("difficulty_level", "intermediate"),
                estimated_setup_time=sanitized_data.get("estimated_setup_time", 10),
                resource_requirements=sanitized_data.get("resource_requirements"),
                
                # Template metadata
                template_size_mb=sanitized_data.get("template_size_mb", 0.0),
                docker_image_count=sanitized_data.get("docker_image_count", 1),
                network_ports=sanitized_data.get("network_ports"),
                volume_mounts=sanitized_data.get("volume_mounts"),
                environment_variables=sanitized_data.get("environment_variables"),
                
                # Search and discovery
                search_keywords=sanitized_data.get("search_keywords"),
                compatibility_tags=sanitized_data.get("compatibility_tags"),
                minimum_docker_version=sanitized_data.get("minimum_docker_version"),
                supported_architectures=sanitized_data.get("supported_architectures", ["amd64"]),
            )
            
            self.db.add(template)
            self.db.commit()
            self.db.refresh(template)
            
            # Create initial version
            self._create_template_version_enhanced(
                template.id, 
                template.version, 
                template.docker_compose_yaml,
                sanitized_data.get("changelog", "Initial version")
            )
            
            # Initialize performance tracking
            self._initialize_performance_tracking(template.id)
            
            # Invalidate relevant caches
            self._invalidate_template_caches(template.category_id)
            
            logger.info(f"Enhanced template created: {template.id} by user {author_id}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create enhanced template: {e}")
            raise

    def get_template_enhanced(
        self, 
        template_id: int, 
        include_analytics: bool = False,
        include_security: bool = False
    ) -> Optional[MarketplaceTemplate]:
        """
        Get a template by ID with enhanced data and optional analytics.
        
        Args:
            template_id: Template ID to retrieve
            include_analytics: Whether to include performance analytics
            include_security: Whether to include security scan results
            
        Returns:
            MarketplaceTemplate instance with enhanced data or None
        """
        try:
            query = (
                self.db.query(MarketplaceTemplate)
                .options(
                    joinedload(MarketplaceTemplate.author),
                    joinedload(MarketplaceTemplate.category),
                    joinedload(MarketplaceTemplate.reviews),
                    joinedload(MarketplaceTemplate.versions),
                )
                .filter(MarketplaceTemplate.id == template_id)
            )
            
            template = query.first()
            if not template:
                return None
            
            # Add analytics data if requested
            if include_analytics:
                template.analytics_data = self._get_template_analytics(template_id)
            
            # Add security data if requested
            if include_security:
                template.security_data = self._get_template_security_data(template_id)
            
            # Update view/access tracking
            self._track_template_access(template_id)
            
            return template
            
        except Exception as e:
            logger.error(f"Failed to get enhanced template {template_id}: {e}")
            return None

    def update_template_enhanced(
        self, 
        template_id: int, 
        template_data: Dict[str, Any], 
        user_id: int,
        create_version: bool = True
    ) -> Optional[MarketplaceTemplate]:
        """
        Update a template with enhanced fields and version management.
        
        Args:
            template_id: Template ID to update
            template_data: Update data with enhanced fields
            user_id: ID of the user performing the update
            create_version: Whether to create a new version
            
        Returns:
            Updated MarketplaceTemplate instance or None
        """
        try:
            template = self.db.query(MarketplaceTemplate).filter(
                MarketplaceTemplate.id == template_id
            ).first()
            
            if not template:
                return None
                
            # Check ownership (will be enforced at router level)
            if template.author_id != user_id:
                return None
            
            # Sanitize and validate update data
            sanitized_data = self._sanitize_template_data(template_data)
            
            # Create new version if Docker Compose changed and requested
            if create_version and "docker_compose_yaml" in sanitized_data:
                new_version = self._increment_version(template.version)
                self._create_template_version_enhanced(
                    template_id,
                    new_version,
                    sanitized_data["docker_compose_yaml"],
                    sanitized_data.get("changelog", f"Updated to version {new_version}")
                )
                sanitized_data["version"] = new_version
            
            # Update template fields
            for field, value in sanitized_data.items():
                if hasattr(template, field) and field not in ["id", "author_id", "created_at"]:
                    setattr(template, field, value)
            
            template.updated_at = datetime.utcnow()
            
            # Re-analyze metadata if Docker Compose changed
            if "docker_compose_yaml" in sanitized_data:
                metadata = self._analyze_template_metadata(sanitized_data["docker_compose_yaml"])
                for field, value in metadata.items():
                    if hasattr(template, field):
                        setattr(template, field, value)
            
            self.db.commit()
            self.db.refresh(template)
            
            # Invalidate relevant caches
            self._invalidate_template_caches(template.category_id, template_id)
            
            logger.info(f"Enhanced template updated: {template_id} by user {user_id}")
            return template
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update enhanced template {template_id}: {e}")
            return None

    def delete_template_enhanced(self, template_id: int, user_id: int) -> bool:
        """
        Delete a template with comprehensive cleanup.
        
        Args:
            template_id: Template ID to delete
            user_id: ID of the user performing the deletion
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            template = self.db.query(MarketplaceTemplate).filter(
                MarketplaceTemplate.id == template_id
            ).first()
            
            if not template:
                return False
                
            # Check ownership (will be enforced at router level)
            if template.author_id != user_id:
                return False
            
            # Store category for cache invalidation
            category_id = template.category_id
            
            # Delete related data (cascading should handle most of this)
            self.db.query(TemplateAnalytics).filter(
                TemplateAnalytics.template_id == template_id
            ).delete()
            
            self.db.query(TemplatePerformanceMetrics).filter(
                TemplatePerformanceMetrics.template_id == template_id
            ).delete()
            
            self.db.query(TemplateSecurityScan).filter(
                TemplateSecurityScan.template_id == template_id
            ).delete()
            
            self.db.query(TemplateDeploymentHistory).filter(
                TemplateDeploymentHistory.template_id == template_id
            ).delete()
            
            # Delete the template (this will cascade to reviews and versions)
            self.db.delete(template)
            self.db.commit()
            
            # Invalidate relevant caches
            self._invalidate_template_caches(category_id, template_id)
            
            logger.info(f"Enhanced template deleted: {template_id} by user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete enhanced template {template_id}: {e}")
            return False

    # ===== ENHANCED SEARCH AND FILTERING =====

    def search_templates_enhanced(
        self,
        search_params: Dict[str, Any],
        use_cache: bool = True,
        performance_sort: bool = False
    ) -> Tuple[List[MarketplaceTemplate], int, Dict[str, Any]]:
        """
        Enhanced template search with advanced filtering, caching, and performance sorting.

        Args:
            search_params: Search parameters including query, filters, pagination
            use_cache: Whether to use caching for search results
            performance_sort: Whether to sort by performance metrics

        Returns:
            Tuple of (templates, total_count, metadata)
        """
        try:
            # Generate cache key for search
            cache_key = self._generate_search_cache_key(search_params, performance_sort)

            # Try to get from cache first
            if use_cache:
                cached_result = self._get_cached_search_result(cache_key)
                if cached_result:
                    return cached_result

            # Build base query with enhanced joins
            query = self.db.query(MarketplaceTemplate).options(
                joinedload(MarketplaceTemplate.author),
                joinedload(MarketplaceTemplate.category),
            )

            # Filter by status (only show approved templates to regular users)
            query = query.filter(MarketplaceTemplate.status == TemplateStatus.APPROVED)

            # Apply enhanced search filters
            query = self._apply_enhanced_search_filters(query, search_params)

            # Get total count before pagination
            total_count = query.count()

            # Apply sorting
            if performance_sort:
                query = self._apply_performance_sorting(query)
            else:
                query = self._apply_standard_sorting(query, search_params.get("sort_by", "created_at"))

            # Apply pagination
            page = search_params.get("page", 1)
            per_page = min(search_params.get("per_page", 20), 100)  # Max 100 per page
            offset = (page - 1) * per_page

            templates = query.offset(offset).limit(per_page).all()

            # Generate search metadata
            metadata = self._generate_search_metadata(search_params, total_count, page, per_page)

            # Cache the result
            if use_cache:
                self._cache_search_result(cache_key, (templates, total_count, metadata))

            return templates, total_count, metadata

        except Exception as e:
            logger.error(f"Failed to search enhanced templates: {e}")
            return [], 0, {}

    def get_featured_templates(self, limit: int = 10) -> List[MarketplaceTemplate]:
        """
        Get featured templates with performance metrics.

        Args:
            limit: Maximum number of templates to return

        Returns:
            List of featured MarketplaceTemplate instances
        """
        try:
            return (
                self.db.query(MarketplaceTemplate)
                .options(
                    joinedload(MarketplaceTemplate.author),
                    joinedload(MarketplaceTemplate.category),
                )
                .filter(
                    and_(
                        MarketplaceTemplate.status == TemplateStatus.APPROVED,
                        MarketplaceTemplate.is_featured == True
                    )
                )
                .order_by(
                    desc(MarketplaceTemplate.performance_score),
                    desc(MarketplaceTemplate.downloads)
                )
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Failed to get featured templates: {e}")
            return []

    def get_recommended_templates(
        self,
        user_id: Optional[int] = None,
        category_id: Optional[int] = None,
        limit: int = 10
    ) -> List[MarketplaceTemplate]:
        """
        Get recommended templates based on user history and performance.

        Args:
            user_id: User ID for personalized recommendations
            category_id: Category ID for category-based recommendations
            limit: Maximum number of templates to return

        Returns:
            List of recommended MarketplaceTemplate instances
        """
        try:
            query = (
                self.db.query(MarketplaceTemplate)
                .options(
                    joinedload(MarketplaceTemplate.author),
                    joinedload(MarketplaceTemplate.category),
                )
                .filter(MarketplaceTemplate.status == TemplateStatus.APPROVED)
            )

            # Apply category filter if provided
            if category_id:
                query = query.filter(MarketplaceTemplate.category_id == category_id)

            # Apply user-based filtering if user provided
            if user_id:
                # Exclude templates the user has already deployed
                deployed_template_ids = (
                    self.db.query(TemplateDeploymentHistory.template_id)
                    .filter(TemplateDeploymentHistory.user_id == user_id)
                    .distinct()
                    .subquery()
                )
                query = query.filter(~MarketplaceTemplate.id.in_(deployed_template_ids))

            # Sort by performance and popularity
            return (
                query.order_by(
                    desc(MarketplaceTemplate.performance_score),
                    desc(MarketplaceTemplate.deployment_success_rate),
                    desc(MarketplaceTemplate.rating_avg),
                    desc(MarketplaceTemplate.downloads)
                )
                .limit(limit)
                .all()
            )

        except Exception as e:
            logger.error(f"Failed to get recommended templates: {e}")
            return []

    # ===== TEMPLATE LIFECYCLE MANAGEMENT =====

    def feature_template(self, template_id: int, admin_id: int) -> bool:
        """Mark a template as featured."""
        try:
            template = self.db.query(MarketplaceTemplate).filter(
                MarketplaceTemplate.id == template_id
            ).first()

            if not template:
                return False

            template.is_featured = True
            template.updated_at = datetime.utcnow()
            self.db.commit()

            self._invalidate_template_caches(template.category_id, template_id)
            logger.info(f"Template {template_id} featured by admin {admin_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to feature template {template_id}: {e}")
            return False

    def deprecate_template(
        self,
        template_id: int,
        reason: str,
        replacement_id: Optional[int] = None,
        admin_id: Optional[int] = None
    ) -> bool:
        """Mark a template as deprecated with optional replacement."""
        try:
            template = self.db.query(MarketplaceTemplate).filter(
                MarketplaceTemplate.id == template_id
            ).first()

            if not template:
                return False

            template.is_deprecated = True
            template.deprecation_reason = html.escape(reason)
            template.replacement_template_id = replacement_id
            template.updated_at = datetime.utcnow()
            self.db.commit()

            self._invalidate_template_caches(template.category_id, template_id)
            logger.info(f"Template {template_id} deprecated by admin {admin_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to deprecate template {template_id}: {e}")
            return False

    # ===== HELPER METHODS =====

    def _sanitize_template_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize template data to prevent XSS and other security issues."""
        sanitized = {}

        # String fields that need HTML escaping
        string_fields = ["name", "description", "subcategory", "search_keywords", "deprecation_reason"]

        for key, value in data.items():
            if key in string_fields and isinstance(value, str):
                sanitized[key] = html.escape(value.strip())
            elif isinstance(value, str):
                sanitized[key] = value.strip()
            else:
                sanitized[key] = value

        return sanitized

    def _validate_docker_compose_enhanced(self, docker_compose_yaml: str) -> None:
        """Enhanced validation of Docker Compose YAML with security checks."""
        if not docker_compose_yaml or len(docker_compose_yaml.strip()) < 50:
            raise ValueError("Docker Compose YAML must be at least 50 characters")

        # Basic YAML structure validation
        try:
            import yaml
            parsed = yaml.safe_load(docker_compose_yaml)
            if not isinstance(parsed, dict):
                raise ValueError("Docker Compose YAML must be a valid YAML object")

            # Check for required version
            if "version" not in parsed and "services" not in parsed:
                raise ValueError("Docker Compose YAML must contain 'version' and 'services'")

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")

        # Security checks
        self._validate_docker_compose_security(docker_compose_yaml)

    def _validate_docker_compose_security(self, docker_compose_yaml: str) -> None:
        """Validate Docker Compose for security issues."""
        # Check for privileged mode
        if "privileged: true" in docker_compose_yaml:
            logger.warning("Template contains privileged containers")

        # Check for host network mode
        if "network_mode: host" in docker_compose_yaml:
            logger.warning("Template uses host network mode")

        # Check for volume mounts to sensitive paths
        sensitive_paths = ["/", "/etc", "/var/run/docker.sock", "/proc", "/sys"]
        for path in sensitive_paths:
            if f":{path}" in docker_compose_yaml:
                logger.warning(f"Template mounts sensitive path: {path}")

    def _analyze_template_metadata(self, docker_compose_yaml: str) -> Dict[str, Any]:
        """Analyze Docker Compose YAML to extract metadata."""
        metadata = {}

        try:
            import yaml
            parsed = yaml.safe_load(docker_compose_yaml)

            if isinstance(parsed, dict) and "services" in parsed:
                services = parsed["services"]

                # Count Docker images
                metadata["docker_image_count"] = len(services)

                # Extract network ports
                ports = []
                for service_name, service_config in services.items():
                    if isinstance(service_config, dict) and "ports" in service_config:
                        ports.extend(service_config["ports"])
                metadata["network_ports"] = ports

                # Extract volume mounts
                volumes = []
                for service_name, service_config in services.items():
                    if isinstance(service_config, dict) and "volumes" in service_config:
                        volumes.extend(service_config["volumes"])
                metadata["volume_mounts"] = volumes

                # Extract environment variables
                env_vars = []
                for service_name, service_config in services.items():
                    if isinstance(service_config, dict) and "environment" in service_config:
                        env_vars.extend(service_config["environment"])
                metadata["environment_variables"] = env_vars

                # Estimate template size (rough calculation)
                metadata["template_size_mb"] = round(len(docker_compose_yaml) / 1024 / 1024, 2)

        except Exception as e:
            logger.warning(f"Failed to analyze template metadata: {e}")

        return metadata

    def _create_template_version_enhanced(
        self,
        template_id: int,
        version: str,
        docker_compose_yaml: str,
        changelog: str = ""
    ) -> None:
        """Create a new template version with enhanced metadata."""
        try:
            version_entry = TemplateVersion(
                template_id=template_id,
                version_number=version,
                docker_compose_yaml=docker_compose_yaml,
                changelog=changelog
            )
            self.db.add(version_entry)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to create template version: {e}")
            raise

    def _increment_version(self, current_version: str) -> str:
        """Increment version number (simple semantic versioning)."""
        try:
            parts = current_version.split(".")
            if len(parts) >= 3:
                # Increment patch version
                parts[2] = str(int(parts[2]) + 1)
            elif len(parts) == 2:
                # Add patch version
                parts.append("1")
            else:
                # Default increment
                return f"{current_version}.1"

            return ".".join(parts)

        except Exception:
            # Fallback to timestamp-based version
            return f"{current_version}.{int(datetime.utcnow().timestamp())}"

    def _initialize_performance_tracking(self, template_id: int) -> None:
        """Initialize performance tracking for a new template."""
        try:
            # Create initial performance metrics entry
            metrics = TemplatePerformanceMetrics(
                template_id=template_id,
                aggregation_period="daily",
                period_start=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
                period_end=datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999),
                total_deployments=0,
                successful_deployments=0,
                failed_deployments=0
            )
            self.db.add(metrics)
            self.db.commit()

        except Exception as e:
            logger.warning(f"Failed to initialize performance tracking for template {template_id}: {e}")

    def _track_template_access(self, template_id: int) -> None:
        """Track template access for analytics."""
        try:
            # This could be enhanced to track user-specific access patterns
            # For now, we'll just log the access
            logger.debug(f"Template {template_id} accessed")

        except Exception as e:
            logger.warning(f"Failed to track template access: {e}")

    def _get_template_analytics(self, template_id: int) -> Dict[str, Any]:
        """Get analytics data for a template."""
        try:
            # Get recent analytics data
            analytics = (
                self.db.query(TemplateAnalytics)
                .filter(TemplateAnalytics.template_id == template_id)
                .order_by(desc(TemplateAnalytics.created_at))
                .limit(10)
                .all()
            )

            # Get performance metrics
            performance = (
                self.db.query(TemplatePerformanceMetrics)
                .filter(TemplatePerformanceMetrics.template_id == template_id)
                .order_by(desc(TemplatePerformanceMetrics.period_start))
                .first()
            )

            return {
                "recent_deployments": len(analytics),
                "avg_performance_score": sum(a.performance_score or 0 for a in analytics) / len(analytics) if analytics else 0,
                "success_rate": performance.success_rate_percentage if performance else 0,
                "total_deployments": performance.total_deployments if performance else 0
            }

        except Exception as e:
            logger.warning(f"Failed to get template analytics: {e}")
            return {}

    def _get_template_security_data(self, template_id: int) -> Dict[str, Any]:
        """Get security data for a template."""
        try:
            # Get latest security scan
            security_scan = (
                self.db.query(TemplateSecurityScan)
                .filter(TemplateSecurityScan.template_id == template_id)
                .order_by(desc(TemplateSecurityScan.scan_completed_at))
                .first()
            )

            if security_scan:
                return {
                    "security_score": security_scan.overall_security_score,
                    "vulnerability_count": (
                        security_scan.vulnerability_count_critical +
                        security_scan.vulnerability_count_high +
                        security_scan.vulnerability_count_medium +
                        security_scan.vulnerability_count_low
                    ),
                    "last_scan": security_scan.scan_completed_at,
                    "scan_status": security_scan.scan_status
                }

            return {"security_score": 0, "vulnerability_count": 0, "last_scan": None}

        except Exception as e:
            logger.warning(f"Failed to get template security data: {e}")
            return {}

    def _generate_search_cache_key(self, search_params: Dict[str, Any], performance_sort: bool) -> str:
        """Generate cache key for search results."""
        # Create a deterministic cache key from search parameters
        key_parts = [
            f"query:{search_params.get('query', '')}",
            f"category:{search_params.get('category_id', '')}",
            f"subcategory:{search_params.get('subcategory', '')}",
            f"difficulty:{search_params.get('difficulty_level', '')}",
            f"sort:{search_params.get('sort_by', 'created_at')}",
            f"perf_sort:{performance_sort}",
            f"page:{search_params.get('page', 1)}",
            f"per_page:{search_params.get('per_page', 20)}"
        ]

        import hashlib
        key_string = "|".join(key_parts)
        return f"template_search:{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_cached_search_result(self, cache_key: str) -> Optional[Tuple[List[MarketplaceTemplate], int, Dict[str, Any]]]:
        """Get cached search result if available and not expired."""
        try:
            cache_entry = (
                self.db.query(TemplateMarketplaceCache)
                .filter(
                    and_(
                        TemplateMarketplaceCache.cache_key == cache_key,
                        TemplateMarketplaceCache.expires_at > datetime.utcnow(),
                        TemplateMarketplaceCache.is_expired == False
                    )
                )
                .first()
            )

            if cache_entry:
                # Update hit count
                cache_entry.hit_count += 1
                cache_entry.last_hit_at = datetime.utcnow()
                self.db.commit()

                # Return cached data (would need proper deserialization in production)
                return cache_entry.cache_value

            return None

        except Exception as e:
            logger.warning(f"Failed to get cached search result: {e}")
            return None

    def _cache_search_result(
        self,
        cache_key: str,
        result: Tuple[List[MarketplaceTemplate], int, Dict[str, Any]]
    ) -> None:
        """Cache search result for future use."""
        try:
            # Calculate cache expiration
            expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)

            # Create cache entry
            cache_entry = TemplateMarketplaceCache(
                cache_key=cache_key,
                cache_value=result,  # In production, this would need proper serialization
                cache_type="search_result",
                expires_at=expires_at,
                ttl_seconds=self.cache_ttl
            )

            self.db.add(cache_entry)
            self.db.commit()

        except Exception as e:
            logger.warning(f"Failed to cache search result: {e}")

    def _invalidate_template_caches(self, category_id: Optional[int] = None, template_id: Optional[int] = None) -> None:
        """Invalidate relevant caches when templates are modified."""
        try:
            # Mark cache entries as expired
            query = self.db.query(TemplateMarketplaceCache)

            if category_id:
                # Invalidate category-related caches
                query = query.filter(
                    or_(
                        TemplateMarketplaceCache.cache_key.like(f"%category:{category_id}%"),
                        TemplateMarketplaceCache.cache_key.like("%category:%")  # General category searches
                    )
                )

            if template_id:
                # Invalidate template-specific caches
                query = query.filter(
                    TemplateMarketplaceCache.template_ids.contains([template_id])
                )

            # Mark as expired
            query.update({"is_expired": True}, synchronize_session=False)
            self.db.commit()

        except Exception as e:
            logger.warning(f"Failed to invalidate template caches: {e}")

    def _apply_enhanced_search_filters(self, query, search_params: Dict[str, Any]):
        """Apply enhanced search filters to the query."""
        # Text search
        if search_params.get("query"):
            search_term = f"%{search_params['query']}%"
            query = query.filter(
                or_(
                    MarketplaceTemplate.name.ilike(search_term),
                    MarketplaceTemplate.description.ilike(search_term),
                    MarketplaceTemplate.search_keywords.ilike(search_term)
                )
            )

        # Category filter
        if search_params.get("category_id"):
            query = query.filter(MarketplaceTemplate.category_id == search_params["category_id"])

        # Subcategory filter
        if search_params.get("subcategory"):
            query = query.filter(MarketplaceTemplate.subcategory == search_params["subcategory"])

        # Difficulty level filter
        if search_params.get("difficulty_level"):
            query = query.filter(MarketplaceTemplate.difficulty_level == search_params["difficulty_level"])

        # Performance score filter
        if search_params.get("min_performance_score"):
            query = query.filter(MarketplaceTemplate.performance_score >= search_params["min_performance_score"])

        # Security score filter
        if search_params.get("min_security_score"):
            query = query.filter(MarketplaceTemplate.security_score >= search_params["min_security_score"])

        # Featured templates only
        if search_params.get("featured_only"):
            query = query.filter(MarketplaceTemplate.is_featured == True)

        # Exclude deprecated templates
        if not search_params.get("include_deprecated", False):
            query = query.filter(MarketplaceTemplate.is_deprecated == False)

        return query

    def _apply_performance_sorting(self, query):
        """Apply performance-based sorting to the query."""
        return query.order_by(
            desc(MarketplaceTemplate.performance_score),
            desc(MarketplaceTemplate.deployment_success_rate),
            desc(MarketplaceTemplate.rating_avg),
            desc(MarketplaceTemplate.downloads)
        )

    def _apply_standard_sorting(self, query, sort_by: str):
        """Apply standard sorting to the query."""
        sort_options = {
            "created_at": desc(MarketplaceTemplate.created_at),
            "updated_at": desc(MarketplaceTemplate.updated_at),
            "name": MarketplaceTemplate.name,
            "downloads": desc(MarketplaceTemplate.downloads),
            "rating": desc(MarketplaceTemplate.rating_avg),
            "performance": desc(MarketplaceTemplate.performance_score)
        }

        sort_field = sort_options.get(sort_by, desc(MarketplaceTemplate.created_at))
        return query.order_by(sort_field)

    def _generate_search_metadata(
        self,
        search_params: Dict[str, Any],
        total_count: int,
        page: int,
        per_page: int
    ) -> Dict[str, Any]:
        """Generate metadata for search results."""
        total_pages = (total_count + per_page - 1) // per_page

        return {
            "total_count": total_count,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "search_params": search_params,
            "generated_at": datetime.utcnow().isoformat()
        }
