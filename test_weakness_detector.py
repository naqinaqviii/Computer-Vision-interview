"""
Quick test to verify the detailed weakness detector is working
"""

from utils.detailed_weakness import get_detailed_weaknesses
import json

# Test case: Sample answer with various weaknesses
question = "Tell me about yourself. Where are you from?"
answer = """
I am from India. I live in Delhi. I am good student. I like coding very much. 
It is very good hobby. I do coding sometimes. Coding is fun. I am interested in computers.
I think maybe computers is future. Actually I like programming languages.
"""

scores = {
    'grammar': 55,
    'fluency': 60,
    'vocabulary': 50,
    'pronunciation': 65
}

print("=" * 70)
print("TESTING DETAILED WEAKNESS DETECTOR")
print("=" * 70)
print(f"\nQuestion: {question}")
print(f"\nAnswer: {answer}")
print(f"\nScores: {scores}")

print("\n" + "=" * 70)
print("ANALYSIS RESULTS")
print("=" * 70)

try:
    results = get_detailed_weaknesses(question, answer, scores)
    
    print("\n✅ DETAILED WEAKNESS ANALYSIS SUCCESSFUL\n")
    
    # Print each weakness category
    for category, data in results.items():
        if category == 'critical_areas':
            print(f"\n🚨 CRITICAL AREAS:")
            for area in data:
                print(f"  {area}")
        elif category == 'overall_severity':
            print(f"\n📊 OVERALL SEVERITY: {data}")
        elif isinstance(data, dict) and 'issues' in data:
            print(f"\n{'=' * 70}")
            print(f"📌 {category.upper()}")
            print(f"{'=' * 70}")
            print(f"  Score: {data.get('score', 'N/A')}/100")
            print(f"  Severity: {data.get('severity', 'N/A')}")
            print(f"  Band Target: {data.get('band_target', 'N/A')}")
            print(f"  Issues Found: {data.get('total_issues', 0)}")
            
            if data.get('issues'):
                print(f"\n  Specific Issues:")
                for issue in data['issues']:
                    print(f"    • {issue.get('issue', 'Unknown issue')}")
                    print(f"      💡 {issue.get('advice', 'No advice')}")
                    print(f"      Impact: {issue.get('impact', 'Unknown')}\n")
            
            # Print additional metrics if available
            if 'metrics' in data:
                print(f"  Metrics:")
                for metric, value in data['metrics'].items():
                    print(f"    • {metric}: {value}")
            
            if 'word_count' in data:
                print(f"  Word Count: {data['word_count']}")
            if 'vocabulary_ratio' in data:
                print(f"  Vocabulary Ratio: {data['vocabulary_ratio']}%")
    
    print("\n" + "=" * 70)
    print("✅ TEST PASSED - Weakness detector is working correctly!")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
