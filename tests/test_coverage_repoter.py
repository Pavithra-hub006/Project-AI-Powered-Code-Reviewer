def compute_coverage(results, threshold=0):
    """
    Compute docstring coverage for parsed results.

    Args:
        results (list): Parsed output from parse_path
        threshold (int): Coverage threshold percentage

    Returns:
        dict: Coverage report
    """

    total_functions = 0
    documented = 0
    files_report = {}

    for r in results:
        file_path = str(r.get("path"))
        funcs = r.get("functions", [])

        file_total = len(funcs)
        file_docs = sum(1 for f in funcs if f.get("has_docstring"))

        total_functions += file_total
        documented += file_docs

        coverage = (
            round((file_docs / file_total) * 100, 2)
            if file_total > 0 else 0
        )

        files_report[file_path] = {
            "total_functions": file_total,
            "documented": file_docs,
            "coverage_percent": coverage,
        }

    coverage_percent = (
        round((documented / total_functions) * 100, 2)
        if total_functions > 0 else 0
    )

    aggregate = {
        "total_functions": total_functions,
        "documented": documented,
        "coverage_percent": coverage_percent,
        "meets_threshold": coverage_percent >= threshold,
    }

    return {
        "aggregate": aggregate,
        "files": files_report
    }

    # """Tests for coverage reporter."""

# from core.reporter.coverage_reporter import compute_coverage
# from core.parser.python_parser import parse_path


# def test_coverage_keys_exist():
#     """Test coverage report structure."""
#     parsed = parse_path("examples")
#     report = compute_coverage(parsed)
    
#     assert "aggregate" in report
#     assert "coverage_percent" in report["aggregate"]
#     assert "total_functions" in report["aggregate"]
#     assert "documented" in report["aggregate"]


# def test_coverage_threshold_check():
#     """Test threshold checking in coverage report."""
#     parsed = parse_path("examples")
#     report = compute_coverage(parsed, threshold=90)
    
#     assert "meets_threshold" in report["aggregate"]
#     assert isinstance(report["aggregate"]["meets_threshold"], bool)


# def test_empty_input_handling():
#     """Test coverage computation with empty input."""
#     report = compute_coverage([])
#     assert report["aggregate"]["total_functions"] == 0
#     assert report["aggregate"]["coverage_percent"] == 0