#!/usr/bin/env python3
"""
Performance Report Generator for Template Marketplace.

This script compiles comprehensive performance test results with metrics,
identifies bottlenecks, provides optimization recommendations, and documents
production readiness assessment.
"""

import json
import time
import glob
import os
from typing import Dict, List, Any
from datetime import datetime


class PerformanceReportGenerator:
    """Generator for comprehensive performance reports."""
    
    def __init__(self):
        """Initialize the report generator."""
        self.report_data = {
            "generated_at": datetime.now().isoformat(),
            "test_summary": {},
            "detailed_results": {},
            "performance_metrics": {},
            "bottlenecks": [],
            "recommendations": [],
            "production_readiness": {}
        }
    
    def load_test_results(self) -> Dict[str, Any]:
        """Load all available test result files."""
        print("📊 Loading Performance Test Results")
        print("=" * 40)
        
        result_files = {
            "api_response_time": glob.glob("api_response_validation_*.json"),
            "concurrent_load": glob.glob("concurrent_load_test_results_*.json"),
            "database_performance": glob.glob("database_performance_test_*.json"),
            "rate_limiting": glob.glob("rate_limiting_validation_*.json")
        }
        
        loaded_results = {}
        
        for test_type, files in result_files.items():
            if files:
                # Get the most recent file
                latest_file = max(files, key=os.path.getctime)
                try:
                    with open(latest_file, 'r') as f:
                        data = json.load(f)
                    loaded_results[test_type] = data
                    print(f"  ✅ Loaded {test_type}: {latest_file}")
                except Exception as e:
                    print(f"  ❌ Failed to load {test_type}: {e}")
            else:
                print(f"  ⚠️ No results found for {test_type}")
        
        return loaded_results
    
    def analyze_api_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze API performance metrics."""
        api_data = results.get("api_response_time", {})
        
        if not api_data:
            return {"status": "No API performance data available"}
        
        # Extract key metrics
        metrics = {
            "endpoints_tested": api_data.get("overall_metrics", {}).get("endpoints_tested", 0),
            "avg_response_time": api_data.get("overall_metrics", {}).get("avg_response_time", 0),
            "success_rate": api_data.get("overall_metrics", {}).get("success_rate", 0),
            "under_200ms_percentage": api_data.get("overall_metrics", {}).get("under_200ms_percentage", 0),
            "middleware_working": api_data.get("overall_metrics", {}).get("middleware_working_count", 0)
        }
        
        # Performance assessment
        performance_grade = "A+"
        if metrics["avg_response_time"] > 100:
            performance_grade = "B+"
        elif metrics["avg_response_time"] > 200:
            performance_grade = "C"
        
        return {
            "status": "Available",
            "metrics": metrics,
            "performance_grade": performance_grade,
            "meets_targets": metrics["avg_response_time"] < 200 and metrics["success_rate"] >= 95
        }
    
    def analyze_load_testing(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze concurrent load testing results."""
        load_data = results.get("concurrent_load", {})
        
        if not load_data:
            return {"status": "No load testing data available"}
        
        # Extract key metrics
        metrics = {
            "concurrent_users": load_data.get("concurrent_users", 0),
            "total_requests": load_data.get("total_requests", 0),
            "requests_per_second": load_data.get("requests_per_second", 0),
            "error_rate": load_data.get("error_rate", 0),
            "avg_response_time": load_data.get("response_times", {}).get("avg", 0),
            "p95_response_time": load_data.get("response_times", {}).get("p95", 0),
            "resource_usage": load_data.get("resource_usage", {})
        }
        
        # Performance assessment
        performance_grade = "A+"
        if metrics["error_rate"] > 1:
            performance_grade = "C"
        elif metrics["avg_response_time"] > 100:
            performance_grade = "B+"
        
        return {
            "status": "Available",
            "metrics": metrics,
            "performance_grade": performance_grade,
            "meets_targets": metrics["error_rate"] < 1 and metrics["avg_response_time"] < 200
        }
    
    def analyze_database_performance(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze database performance results."""
        db_data = results.get("database_performance", {})
        
        if not db_data:
            return {"status": "No database performance data available"}
        
        # Extract key metrics
        metrics = {
            "total_tests": db_data.get("total_tests", 0),
            "success_rate": db_data.get("success_rate", 0),
            "avg_query_time": db_data.get("overall_avg_time", 0),
            "targets_met": db_data.get("targets_met", 0),
            "total_targets": db_data.get("total_targets", 0),
            "overall_status": db_data.get("overall_status", "Unknown")
        }
        
        # Performance assessment
        performance_grade = "A+"
        if metrics["avg_query_time"] > 50:
            performance_grade = "B+"
        elif metrics["avg_query_time"] > 100:
            performance_grade = "C"
        
        return {
            "status": "Available",
            "metrics": metrics,
            "performance_grade": performance_grade,
            "meets_targets": "EXCELLENT" in metrics["overall_status"]
        }
    
    def identify_bottlenecks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []
        
        # Check API performance bottlenecks
        api_analysis = analysis.get("api_performance", {})
        if api_analysis.get("status") == "Available":
            metrics = api_analysis["metrics"]
            if metrics["avg_response_time"] > 100:
                bottlenecks.append({
                    "category": "API Performance",
                    "severity": "Medium" if metrics["avg_response_time"] < 200 else "High",
                    "issue": f"Average response time {metrics['avg_response_time']:.2f}ms exceeds optimal threshold",
                    "impact": "User experience degradation",
                    "recommendation": "Optimize endpoint logic and consider caching"
                })
        
        # Check load testing bottlenecks
        load_analysis = analysis.get("load_testing", {})
        if load_analysis.get("status") == "Available":
            metrics = load_analysis["metrics"]
            if metrics["error_rate"] > 1:
                bottlenecks.append({
                    "category": "Load Handling",
                    "severity": "High",
                    "issue": f"Error rate {metrics['error_rate']:.2f}% exceeds 1% threshold",
                    "impact": "System reliability under load",
                    "recommendation": "Investigate and fix server-side errors"
                })
            
            # Check resource usage
            resource_usage = metrics.get("resource_usage", {})
            if resource_usage and not resource_usage.get("error"):
                cpu_avg = resource_usage.get("cpu", {}).get("avg", 0)
                memory_avg = resource_usage.get("memory", {}).get("avg", 0)
                
                if cpu_avg > 70:
                    bottlenecks.append({
                        "category": "System Resources",
                        "severity": "Medium",
                        "issue": f"CPU usage {cpu_avg:.1f}% approaching threshold",
                        "impact": "Performance degradation under sustained load",
                        "recommendation": "Consider CPU optimization or scaling"
                    })
                
                if memory_avg > 80:
                    bottlenecks.append({
                        "category": "System Resources",
                        "severity": "Medium",
                        "issue": f"Memory usage {memory_avg:.1f}% approaching threshold",
                        "impact": "Risk of memory exhaustion",
                        "recommendation": "Optimize memory usage or increase allocation"
                    })
        
        return bottlenecks
    
    def generate_recommendations(self, analysis: Dict[str, Any], bottlenecks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations."""
        recommendations = []
        
        # General performance recommendations
        recommendations.extend([
            {
                "category": "Performance Monitoring",
                "priority": "High",
                "recommendation": "Implement continuous performance monitoring in production",
                "rationale": "Real-time performance tracking enables proactive optimization",
                "implementation": "Deploy performance monitoring middleware with alerting"
            },
            {
                "category": "Caching Strategy",
                "priority": "Medium",
                "recommendation": "Implement Redis caching for frequently accessed data",
                "rationale": "Reduce database load and improve response times",
                "implementation": "Cache template listings, categories, and user sessions"
            },
            {
                "category": "Database Optimization",
                "priority": "Low",
                "recommendation": "Monitor query performance and add indexes as needed",
                "rationale": "Maintain optimal database performance as data grows",
                "implementation": "Regular query analysis and index optimization"
            }
        ])
        
        # Bottleneck-specific recommendations
        for bottleneck in bottlenecks:
            if bottleneck["severity"] == "High":
                recommendations.insert(0, {
                    "category": f"{bottleneck['category']} - Critical",
                    "priority": "Critical",
                    "recommendation": bottleneck["recommendation"],
                    "rationale": f"Addresses critical issue: {bottleneck['issue']}",
                    "implementation": "Immediate investigation and resolution required"
                })
        
        return recommendations
    
    def assess_production_readiness(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall production readiness."""
        readiness_scores = {}
        
        # API Performance Score
        api_analysis = analysis.get("api_performance", {})
        if api_analysis.get("meets_targets"):
            readiness_scores["api_performance"] = 100
        elif api_analysis.get("performance_grade") == "B+":
            readiness_scores["api_performance"] = 80
        else:
            readiness_scores["api_performance"] = 60
        
        # Load Testing Score
        load_analysis = analysis.get("load_testing", {})
        if load_analysis.get("meets_targets"):
            readiness_scores["load_handling"] = 100
        elif load_analysis.get("performance_grade") == "B+":
            readiness_scores["load_handling"] = 80
        else:
            readiness_scores["load_handling"] = 60
        
        # Database Performance Score
        db_analysis = analysis.get("database_performance", {})
        if db_analysis.get("meets_targets"):
            readiness_scores["database_performance"] = 100
        elif db_analysis.get("performance_grade") == "B+":
            readiness_scores["database_performance"] = 80
        else:
            readiness_scores["database_performance"] = 60
        
        # Calculate overall score
        overall_score = sum(readiness_scores.values()) / len(readiness_scores) if readiness_scores else 0
        
        # Determine readiness status
        if overall_score >= 95:
            status = "PRODUCTION READY"
            recommendation = "System exceeds production requirements and is ready for deployment"
        elif overall_score >= 80:
            status = "PRODUCTION READY WITH MONITORING"
            recommendation = "System meets production requirements with recommended monitoring"
        elif overall_score >= 70:
            status = "NEEDS MINOR OPTIMIZATION"
            recommendation = "Address identified bottlenecks before production deployment"
        else:
            status = "NEEDS SIGNIFICANT OPTIMIZATION"
            recommendation = "Major performance improvements required before production"
        
        return {
            "overall_score": round(overall_score, 1),
            "status": status,
            "recommendation": recommendation,
            "component_scores": readiness_scores,
            "deployment_approved": overall_score >= 80
        }
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        print("🚀 Generating Comprehensive Performance Report")
        print("=" * 50)
        
        # Load test results
        results = self.load_test_results()
        
        # Analyze performance data
        analysis = {
            "api_performance": self.analyze_api_performance(results),
            "load_testing": self.analyze_load_testing(results),
            "database_performance": self.analyze_database_performance(results)
        }
        
        # Identify bottlenecks and generate recommendations
        bottlenecks = self.identify_bottlenecks(analysis)
        recommendations = self.generate_recommendations(analysis, bottlenecks)
        production_readiness = self.assess_production_readiness(analysis)
        
        # Compile final report
        self.report_data.update({
            "test_summary": {
                "tests_conducted": len([a for a in analysis.values() if a.get("status") == "Available"]),
                "overall_performance_grade": self._calculate_overall_grade(analysis),
                "critical_issues": len([b for b in bottlenecks if b["severity"] == "High"]),
                "recommendations_count": len(recommendations)
            },
            "detailed_results": analysis,
            "performance_metrics": self._extract_key_metrics(analysis),
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "production_readiness": production_readiness
        })
        
        return self.report_data
    
    def _calculate_overall_grade(self, analysis: Dict[str, Any]) -> str:
        """Calculate overall performance grade."""
        grades = []
        for component in analysis.values():
            if component.get("performance_grade"):
                grades.append(component["performance_grade"])
        
        if not grades:
            return "N/A"
        
        # Simple grade calculation (can be enhanced)
        if all(g == "A+" for g in grades):
            return "A+"
        elif all(g in ["A+", "B+"] for g in grades):
            return "B+"
        else:
            return "C"
    
    def _extract_key_metrics(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key performance metrics."""
        metrics = {}
        
        for component, data in analysis.items():
            if data.get("status") == "Available" and "metrics" in data:
                metrics[component] = data["metrics"]
        
        return metrics


def main():
    """Main function to generate performance report."""
    generator = PerformanceReportGenerator()
    
    try:
        # Generate comprehensive report
        report = generator.generate_comprehensive_report()
        
        # Save report to file
        timestamp = int(time.time())
        filename = f"template_marketplace_performance_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Display summary
        print(f"\n📊 PERFORMANCE REPORT SUMMARY")
        print("=" * 50)
        
        summary = report["test_summary"]
        readiness = report["production_readiness"]
        
        print(f"Tests Conducted: {summary['tests_conducted']}")
        print(f"Overall Grade: {summary['overall_performance_grade']}")
        print(f"Critical Issues: {summary['critical_issues']}")
        print(f"Recommendations: {summary['recommendations_count']}")
        print(f"Production Score: {readiness['overall_score']}/100")
        print(f"Status: {readiness['status']}")
        print(f"Deployment Approved: {'✅ YES' if readiness['deployment_approved'] else '❌ NO'}")
        
        print(f"\n📄 Full report saved to: {filename}")
        
        # Return appropriate exit code
        if readiness["deployment_approved"]:
            print("\n🎉 Performance Report: PRODUCTION READY")
            return 0
        else:
            print("\n⚠️ Performance Report: OPTIMIZATION NEEDED")
            return 1
            
    except Exception as e:
        print(f"\n❌ Report generation failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
