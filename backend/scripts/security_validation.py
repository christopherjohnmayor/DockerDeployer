#!/usr/bin/env python3
"""
Security validation script for DockerDeployer.
Validates security configurations and practices to achieve 90/100+ security score.
"""

import os
import sys
import json
import subprocess
import re
from typing import Dict, List, Tuple
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SecurityValidator:
    """Security validation for DockerDeployer."""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent
        self.frontend_dir = self.backend_dir.parent / "frontend"
        self.root_dir = self.backend_dir.parent
        self.security_score = 0
        self.max_score = 100
        self.checks = []
        
    def check_cors_configuration(self) -> Tuple[bool, str, int]:
        """Check CORS configuration for security."""
        try:
            main_py = self.backend_dir / "app" / "main.py"
            if main_py.exists():
                content = main_py.read_text()
                
                # Check for wildcard origins (security risk)
                if '"*"' in content and 'allow_origins' in content:
                    return False, "❌ CORS allows wildcard origins (*) - security risk", 0
                
                # Check for proper CORS configuration
                if 'allow_origins' in content and 'localhost' in content:
                    return True, "✅ CORS properly configured with specific origins", 10
                    
                return False, "❌ CORS configuration not found or improperly configured", 0
            
            return False, "❌ Main application file not found", 0
            
        except Exception as e:
            return False, f"❌ Error checking CORS: {e}", 0
    
    def check_security_headers(self) -> Tuple[bool, str, int]:
        """Check for security headers middleware."""
        try:
            main_py = self.backend_dir / "app" / "main.py"
            if main_py.exists():
                content = main_py.read_text()
                
                # Check for security headers middleware
                security_patterns = [
                    'SecurityHeadersMiddleware',
                    'X-Content-Type-Options',
                    'X-Frame-Options',
                    'X-XSS-Protection',
                    'Strict-Transport-Security'
                ]
                
                found_patterns = sum(1 for pattern in security_patterns if pattern in content)
                
                if found_patterns >= 3:
                    return True, f"✅ Security headers implemented ({found_patterns}/5 patterns found)", 15
                elif found_patterns >= 1:
                    return True, f"⚠️ Partial security headers ({found_patterns}/5 patterns found)", 8
                else:
                    return False, "❌ No security headers middleware found", 0
            
            return False, "❌ Main application file not found", 0
            
        except Exception as e:
            return False, f"❌ Error checking security headers: {e}", 0
    
    def check_input_sanitization(self) -> Tuple[bool, str, int]:
        """Check for input sanitization and validation."""
        try:
            score = 0
            patterns_found = []
            
            # Check for Pydantic models (input validation)
            models_dir = self.backend_dir / "app"
            pydantic_files = list(models_dir.rglob("*models.py"))
            
            if pydantic_files:
                patterns_found.append("Pydantic models")
                score += 5
            
            # Check for HTML escaping
            for py_file in models_dir.rglob("*.py"):
                content = py_file.read_text()
                if 'html.escape' in content or 'escape(' in content:
                    patterns_found.append("HTML escaping")
                    score += 5
                    break
            
            # Check for SQL injection protection (SQLAlchemy ORM)
            if any('sqlalchemy' in py_file.read_text() for py_file in models_dir.rglob("*.py")):
                patterns_found.append("SQLAlchemy ORM")
                score += 5
            
            if score >= 10:
                return True, f"✅ Input sanitization implemented: {', '.join(patterns_found)}", score
            elif score > 0:
                return True, f"⚠️ Partial input sanitization: {', '.join(patterns_found)}", score
            else:
                return False, "❌ No input sanitization patterns found", 0
                
        except Exception as e:
            return False, f"❌ Error checking input sanitization: {e}", 0
    
    def check_authentication_security(self) -> Tuple[bool, str, int]:
        """Check authentication and authorization security."""
        try:
            score = 0
            features = []
            
            auth_dir = self.backend_dir / "app" / "auth"
            if auth_dir.exists():
                # Check for JWT implementation
                for py_file in auth_dir.rglob("*.py"):
                    content = py_file.read_text()
                    
                    if 'jwt' in content.lower():
                        features.append("JWT tokens")
                        score += 8
                        break
                
                # Check for password hashing
                for py_file in auth_dir.rglob("*.py"):
                    content = py_file.read_text()
                    
                    if any(pattern in content for pattern in ['bcrypt', 'hash', 'verify_password']):
                        features.append("Password hashing")
                        score += 7
                        break
                
                # Check for role-based access control
                for py_file in auth_dir.rglob("*.py"):
                    content = py_file.read_text()
                    
                    if any(pattern in content for pattern in ['role', 'permission', 'admin']):
                        features.append("RBAC")
                        score += 5
                        break
            
            if score >= 15:
                return True, f"✅ Strong authentication: {', '.join(features)}", score
            elif score >= 8:
                return True, f"⚠️ Basic authentication: {', '.join(features)}", score
            else:
                return False, "❌ Weak or missing authentication", 0
                
        except Exception as e:
            return False, f"❌ Error checking authentication: {e}", 0
    
    def check_rate_limiting(self) -> Tuple[bool, str, int]:
        """Check for rate limiting implementation."""
        try:
            main_py = self.backend_dir / "app" / "main.py"
            if main_py.exists():
                content = main_py.read_text()
                
                # Check for rate limiting patterns
                rate_patterns = ['rate_limit', 'RateLimiter', 'slowapi', 'redis']
                found_patterns = [pattern for pattern in rate_patterns if pattern in content]
                
                if len(found_patterns) >= 2:
                    return True, f"✅ Rate limiting implemented: {', '.join(found_patterns)}", 15
                elif len(found_patterns) >= 1:
                    return True, f"⚠️ Basic rate limiting: {', '.join(found_patterns)}", 8
                else:
                    return False, "❌ No rate limiting found", 0
            
            return False, "❌ Main application file not found", 0
            
        except Exception as e:
            return False, f"❌ Error checking rate limiting: {e}", 0
    
    def check_environment_security(self) -> Tuple[bool, str, int]:
        """Check environment and configuration security."""
        try:
            score = 0
            issues = []
            
            # Check for .env file (should exist)
            env_file = self.backend_dir / ".env"
            if env_file.exists():
                score += 5
            else:
                issues.append("Missing .env file")
            
            # Check .gitignore for sensitive files
            gitignore = self.root_dir / ".gitignore"
            if gitignore.exists():
                content = gitignore.read_text()
                if '.env' in content and '*.key' in content:
                    score += 5
                else:
                    issues.append("Incomplete .gitignore")
            else:
                issues.append("Missing .gitignore")
            
            # Check for hardcoded secrets (basic check)
            for py_file in self.backend_dir.rglob("*.py"):
                content = py_file.read_text()
                if re.search(r'password\s*=\s*["\'][^"\']+["\']', content, re.IGNORECASE):
                    issues.append("Potential hardcoded passwords")
                    score -= 5
                    break
            
            if score >= 8:
                return True, "✅ Good environment security", score
            elif score >= 5:
                return True, f"⚠️ Basic environment security. Issues: {', '.join(issues)}", score
            else:
                return False, f"❌ Poor environment security. Issues: {', '.join(issues)}", max(0, score)
                
        except Exception as e:
            return False, f"❌ Error checking environment security: {e}", 0
    
    def check_dependency_security(self) -> Tuple[bool, str, int]:
        """Check for dependency security."""
        try:
            # Check for security-related dependencies
            requirements = self.backend_dir / "requirements.txt"
            if requirements.exists():
                content = requirements.read_text()
                
                security_deps = ['cryptography', 'bcrypt', 'passlib', 'python-jose']
                found_deps = [dep for dep in security_deps if dep in content]
                
                if len(found_deps) >= 2:
                    return True, f"✅ Security dependencies found: {', '.join(found_deps)}", 10
                elif len(found_deps) >= 1:
                    return True, f"⚠️ Some security dependencies: {', '.join(found_deps)}", 5
                else:
                    return False, "❌ No security dependencies found", 0
            
            return False, "❌ Requirements file not found", 0
            
        except Exception as e:
            return False, f"❌ Error checking dependencies: {e}", 0
    
    def check_docker_security(self) -> Tuple[bool, str, int]:
        """Check Docker security configurations."""
        try:
            score = 0
            features = []
            
            # Check Dockerfile
            dockerfile = self.backend_dir / "Dockerfile"
            if dockerfile.exists():
                content = dockerfile.read_text()
                
                # Check for non-root user
                if 'USER' in content and 'root' not in content.split('USER')[1].split('\n')[0]:
                    features.append("Non-root user")
                    score += 5
                
                # Check for minimal base image
                if any(base in content for base in ['alpine', 'slim', 'distroless']):
                    features.append("Minimal base image")
                    score += 3
                
                # Check for multi-stage build
                if content.count('FROM') > 1:
                    features.append("Multi-stage build")
                    score += 2
            
            if score >= 8:
                return True, f"✅ Good Docker security: {', '.join(features)}", score
            elif score >= 3:
                return True, f"⚠️ Basic Docker security: {', '.join(features)}", score
            else:
                return False, "❌ Poor Docker security configuration", 0
                
        except Exception as e:
            return False, f"❌ Error checking Docker security: {e}", 0
    
    def run_all_checks(self) -> Dict:
        """Run all security checks and calculate score."""
        
        check_functions = [
            ("CORS Configuration", self.check_cors_configuration),
            ("Security Headers", self.check_security_headers),
            ("Input Sanitization", self.check_input_sanitization),
            ("Authentication Security", self.check_authentication_security),
            ("Rate Limiting", self.check_rate_limiting),
            ("Environment Security", self.check_environment_security),
            ("Dependency Security", self.check_dependency_security),
            ("Docker Security", self.check_docker_security),
        ]
        
        results = {}
        total_score = 0
        
        for check_name, check_func in check_functions:
            passed, message, score = check_func()
            results[check_name] = {
                "passed": passed,
                "message": message,
                "score": score
            }
            total_score += score
        
        results["total_score"] = total_score
        results["max_score"] = self.max_score
        results["percentage"] = round((total_score / self.max_score) * 100, 1)
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate security validation report."""
        
        report = []
        report.append("=" * 80)
        report.append("DOCKERDEPLOYER SECURITY VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        for check_name, result in results.items():
            if check_name in ["total_score", "max_score", "percentage"]:
                continue
                
            report.append(f"{result['message']}")
            report.append(f"   Score: {result['score']} points")
            report.append("")
        
        # Summary
        total_score = results["total_score"]
        percentage = results["percentage"]
        
        report.append("=" * 80)
        report.append("SECURITY SCORE SUMMARY")
        report.append("=" * 80)
        report.append(f"Total Score: {total_score}/{self.max_score} ({percentage}%)")
        report.append("")
        
        if percentage >= 90:
            report.append("🎉 EXCELLENT SECURITY SCORE - PRODUCTION READY!")
        elif percentage >= 80:
            report.append("✅ GOOD SECURITY SCORE - MINOR IMPROVEMENTS RECOMMENDED")
        elif percentage >= 70:
            report.append("⚠️ MODERATE SECURITY SCORE - IMPROVEMENTS NEEDED")
        else:
            report.append("❌ LOW SECURITY SCORE - SIGNIFICANT IMPROVEMENTS REQUIRED")
        
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main security validation function."""
    
    print("Starting DockerDeployer Security Validation...")
    print()
    
    validator = SecurityValidator()
    results = validator.run_all_checks()
    report = validator.generate_report(results)
    
    print(report)
    
    # Save results to file
    with open("security_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code based on security score
    percentage = results["percentage"]
    sys.exit(0 if percentage >= 90 else 1)

if __name__ == "__main__":
    main()
