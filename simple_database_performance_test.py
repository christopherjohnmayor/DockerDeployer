#!/usr/bin/env python3
"""
Simple Database Performance Test for Template Marketplace.

This script tests database performance with the seeded marketplace data.
"""

import sqlite3
import time
import statistics
import json
from typing import List, Dict, Any


class SimpleDatabasePerformanceTester:
    """Simple database performance tester using direct SQLite connection."""
    
    def __init__(self, db_path: str = "backend/data/dockerdeployer.db"):
        """Initialize the tester."""
        self.db_path = db_path
        self.connection = None
        
    def connect(self) -> bool:
        """Connect to the database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> tuple:
        """Execute a query and measure execution time."""
        start_time = time.time()
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            rows = cursor.fetchall()
            cursor.close()
            
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            return rows, execution_time, True
            
        except Exception as e:
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000
            print(f"Query execution error: {e}")
            return [], execution_time, False
    
    def test_basic_queries(self) -> Dict[str, Any]:
        """Test basic database queries."""
        print("\n🔍 Testing Basic Database Queries")
        print("=" * 40)
        
        basic_tests = [
            {
                "name": "Count Users",
                "query": "SELECT COUNT(*) FROM users",
                "description": "Count total users in database"
            },
            {
                "name": "Count Templates",
                "query": "SELECT COUNT(*) FROM marketplace_templates",
                "description": "Count total marketplace templates"
            },
            {
                "name": "Count Reviews",
                "query": "SELECT COUNT(*) FROM template_reviews",
                "description": "Count total template reviews"
            },
            {
                "name": "Count Categories",
                "query": "SELECT COUNT(*) FROM template_categories",
                "description": "Count template categories"
            },
            {
                "name": "Count Template Versions",
                "query": "SELECT COUNT(*) FROM template_versions",
                "description": "Count template versions"
            }
        ]
        
        results = []
        
        for test in basic_tests:
            rows, execution_time, success = self.execute_query(test["query"])
            
            if success and rows:
                count = rows[0][0]
                print(f"  ✅ {test['name']}: {count:,} records in {execution_time:.2f}ms")
                
                result = {
                    "test_name": test["name"],
                    "execution_time_ms": round(execution_time, 2),
                    "record_count": count,
                    "success": True
                }
            else:
                print(f"  ❌ {test['name']}: Failed")
                result = {
                    "test_name": test["name"],
                    "execution_time_ms": round(execution_time, 2),
                    "record_count": 0,
                    "success": False
                }
            
            results.append(result)
        
        successful_results = [r for r in results if r["success"]]
        avg_time = statistics.mean([r["execution_time_ms"] for r in successful_results]) if successful_results else 0
        
        return {
            "test_type": "basic_queries",
            "total_tests": len(basic_tests),
            "successful_tests": len(successful_results),
            "avg_execution_time": round(avg_time, 2),
            "results": results
        }
    
    def test_search_queries(self) -> Dict[str, Any]:
        """Test search and filtering queries."""
        print("\n🔍 Testing Search and Filter Queries")
        print("=" * 40)
        
        search_tests = [
            {
                "name": "Search Templates by Name",
                "query": "SELECT * FROM marketplace_templates WHERE name LIKE ? LIMIT 10",
                "params": ('%web%',),
                "description": "Search templates containing 'web'"
            },
            {
                "name": "Filter by Category",
                "query": "SELECT * FROM marketplace_templates WHERE category_id = ? LIMIT 10",
                "params": (1,),
                "description": "Filter templates by category ID"
            },
            {
                "name": "Filter by Status",
                "query": "SELECT * FROM marketplace_templates WHERE status = ? LIMIT 10",
                "params": ('approved',),
                "description": "Filter approved templates"
            },
            {
                "name": "Complex Search with JOIN",
                "query": """
                    SELECT mt.*, tc.name as category_name 
                    FROM marketplace_templates mt 
                    LEFT JOIN template_categories tc ON mt.category_id = tc.id 
                    WHERE mt.status = ? AND mt.name LIKE ? 
                    LIMIT 10
                """,
                "params": ('approved', '%app%'),
                "description": "Complex search with JOIN"
            },
            {
                "name": "Search with Reviews",
                "query": """
                    SELECT mt.name, AVG(tr.rating) as avg_rating, COUNT(tr.id) as review_count
                    FROM marketplace_templates mt
                    LEFT JOIN template_reviews tr ON mt.id = tr.template_id
                    WHERE mt.status = 'approved'
                    GROUP BY mt.id, mt.name
                    HAVING COUNT(tr.id) > 0
                    ORDER BY avg_rating DESC
                    LIMIT 10
                """,
                "params": None,
                "description": "Templates with average ratings"
            }
        ]
        
        results = []
        
        for test in search_tests:
            rows, execution_time, success = self.execute_query(test["query"], test.get("params"))
            
            if success:
                print(f"  ✅ {test['name']}: {len(rows)} results in {execution_time:.2f}ms")
                result = {
                    "test_name": test["name"],
                    "execution_time_ms": round(execution_time, 2),
                    "results_count": len(rows),
                    "success": True
                }
            else:
                print(f"  ❌ {test['name']}: Failed")
                result = {
                    "test_name": test["name"],
                    "execution_time_ms": round(execution_time, 2),
                    "results_count": 0,
                    "success": False
                }
            
            results.append(result)
        
        successful_results = [r for r in results if r["success"]]
        avg_time = statistics.mean([r["execution_time_ms"] for r in successful_results]) if successful_results else 0
        
        return {
            "test_type": "search_queries",
            "total_tests": len(search_tests),
            "successful_tests": len(successful_results),
            "avg_execution_time": round(avg_time, 2),
            "results": results
        }
    
    def test_pagination_queries(self) -> Dict[str, Any]:
        """Test pagination performance."""
        print("\n📄 Testing Pagination Queries")
        print("=" * 40)
        
        page_sizes = [10, 25, 50, 100]
        results = []
        
        for page_size in page_sizes:
            for page_num in [1, 5, 10, 20]:
                offset = (page_num - 1) * page_size
                
                test_name = f"Page {page_num} (size {page_size})"
                query = f"SELECT * FROM marketplace_templates ORDER BY created_at DESC LIMIT {page_size} OFFSET {offset}"
                
                rows, execution_time, success = self.execute_query(query)
                
                if success:
                    print(f"  ✅ {test_name}: {len(rows)} results in {execution_time:.2f}ms")
                    result = {
                        "test_name": test_name,
                        "page_size": page_size,
                        "page_number": page_num,
                        "offset": offset,
                        "execution_time_ms": round(execution_time, 2),
                        "results_count": len(rows),
                        "success": True
                    }
                else:
                    print(f"  ❌ {test_name}: Failed")
                    result = {
                        "test_name": test_name,
                        "page_size": page_size,
                        "page_number": page_num,
                        "offset": offset,
                        "execution_time_ms": round(execution_time, 2),
                        "results_count": 0,
                        "success": False
                    }
                
                results.append(result)
        
        successful_results = [r for r in results if r["success"]]
        avg_time = statistics.mean([r["execution_time_ms"] for r in successful_results]) if successful_results else 0
        
        return {
            "test_type": "pagination_queries",
            "total_tests": len(results),
            "successful_tests": len(successful_results),
            "avg_execution_time": round(avg_time, 2),
            "results": results
        }
    
    def test_index_effectiveness(self) -> Dict[str, Any]:
        """Test database index effectiveness."""
        print("\n📊 Testing Index Effectiveness")
        print("=" * 40)
        
        # Check indexes
        rows, execution_time, success = self.execute_query(
            "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND tbl_name LIKE '%template%'"
        )
        
        if success:
            indexes = [(row[0], row[1]) for row in rows]
            print(f"  ✅ Found {len(indexes)} indexes in {execution_time:.2f}ms")
            for idx_name, table_name in indexes:
                print(f"    - {idx_name} on {table_name}")
        else:
            indexes = []
            print(f"  ❌ Failed to query indexes")
        
        return {
            "test_type": "index_effectiveness",
            "execution_time_ms": round(execution_time, 2),
            "indexes_found": len(indexes),
            "index_details": indexes,
            "success": success
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive database performance test."""
        print("🚀 Database Performance Validation")
        print("=" * 50)
        
        if not self.connect():
            return {"error": "Failed to connect to database"}
        
        start_time = time.time()
        
        # Run all test suites
        test_suites = [
            self.test_basic_queries(),
            self.test_search_queries(),
            self.test_pagination_queries(),
            self.test_index_effectiveness()
        ]
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate overall statistics
        total_tests = sum(suite.get("total_tests", 0) for suite in test_suites if "total_tests" in suite)
        successful_tests = sum(suite.get("successful_tests", 0) for suite in test_suites if "successful_tests" in suite)
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Calculate average execution times
        all_execution_times = []
        for suite in test_suites:
            if suite.get("avg_execution_time"):
                all_execution_times.append(suite["avg_execution_time"])
        
        overall_avg_time = statistics.mean(all_execution_times) if all_execution_times else 0
        
        # Performance assessment
        performance_targets = {
            "avg_query_time_under_50ms": overall_avg_time < 50,
            "success_rate_over_90_percent": success_rate >= 90,
            "basic_queries_fast": any(suite.get("avg_execution_time", 0) < 10 for suite in test_suites if suite.get("test_type") == "basic_queries"),
            "search_queries_efficient": any(suite.get("avg_execution_time", 0) < 100 for suite in test_suites if suite.get("test_type") == "search_queries"),
            "pagination_efficient": any(suite.get("avg_execution_time", 0) < 50 for suite in test_suites if suite.get("test_type") == "pagination_queries")
        }
        
        targets_met = sum(performance_targets.values())
        total_targets = len(performance_targets)
        
        # Overall assessment
        print(f"\n📊 OVERALL DATABASE PERFORMANCE ASSESSMENT")
        print("=" * 50)
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Average Query Time: {overall_avg_time:.2f}ms")
        print("")
        
        print("🎯 Performance Targets:")
        for target, met in performance_targets.items():
            status = "✅" if met else "❌"
            print(f"  {status} {target.replace('_', ' ').title()}")
        print("")
        
        if targets_met == total_targets:
            overall_status = "✅ EXCELLENT"
            recommendation = "Database performance meets production requirements"
        elif targets_met >= total_targets * 0.75:
            overall_status = "⚠️ GOOD"
            recommendation = "Database performance is acceptable with minor optimizations needed"
        else:
            overall_status = "❌ NEEDS IMPROVEMENT"
            recommendation = "Database optimization required before production deployment"
        
        print(f"🏆 Overall Status: {overall_status}")
        print(f"💡 Recommendation: {recommendation}")
        
        # Close connection
        if self.connection:
            self.connection.close()
        
        return {
            "overall_status": overall_status,
            "recommendation": recommendation,
            "total_duration": total_duration,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": success_rate,
            "overall_avg_time": overall_avg_time,
            "targets_met": targets_met,
            "total_targets": total_targets,
            "performance_targets": performance_targets,
            "test_suites": test_suites
        }


def main():
    """Main function to run database performance test."""
    tester = SimpleDatabasePerformanceTester()
    
    try:
        # Run test
        results = tester.run_comprehensive_test()
        
        if results.get("error"):
            print(f"❌ Test failed: {results['error']}")
            return 1
        
        # Save results to file
        timestamp = int(time.time())
        filename = f"database_performance_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed results saved to: {filename}")
        
        # Return appropriate exit code
        if "EXCELLENT" in results.get("overall_status", ""):
            print("\n🎉 Database Performance Test: PASSED")
            return 0
        elif "GOOD" in results.get("overall_status", ""):
            print("\n⚠️ Database Performance Test: ACCEPTABLE")
            return 0
        else:
            print("\n❌ Database Performance Test: NEEDS IMPROVEMENT")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
