"""
Test script for SEM-03 improved structural validation
"""
from app.evaluator.semantica_evaluator import EvaluadorSemanticaTecnica

# Test data simulating a website with structural issues
test_data = {
    'metadata': {
        'title': 'Test Site',
        'has_title': True,
        'lang': 'es',
        'has_lang': True,
        'description': 'Test description for evaluator',
        'has_description': True,
        'keywords': 'gobierno, bolivia, test',
        'has_keywords': True,
        'viewport': 'width=device-width, initial-scale=1',
        'has_viewport': True
    },
    'structure': {
        'has_html5_doctype': True,
        'doctype_text': 'html',
        'has_utf8_charset': True,
        'charset_declared': 'utf-8',
        'obsolete_elements': [],
        'obsolete_attributes': [],
        'has_obsolete_code': False,
        'has_html': True,
        'has_head': True,
        'has_body': True,
        'document_hierarchy': {
            'hierarchy': [
                {
                    'tag': 'header',
                    'depth': 0,
                    'id': None,
                    'class': None,
                    'parent': 'body',
                    'children': [
                        {'tag': 'nav', 'depth': 1, 'id': None, 'class': None, 'parent': 'header', 'children': []}
                    ]
                },
                {
                    'tag': 'section',
                    'depth': 0,
                    'id': None,
                    'class': None,
                    'parent': 'body',
                    'children': [
                        {'tag': 'main', 'depth': 1, 'id': None, 'class': None, 'parent': 'section', 'children': []}
                    ]
                },
                {
                    'tag': 'footer',
                    'depth': 0,
                    'id': None,
                    'class': None,
                    'parent': 'body',
                    'children': []
                }
            ],
            'structure_analysis': {
                'header_count': 1,
                'main_count': 1,
                'footer_count': 1,
                'nav_count': 1,
                'navs_in_header': 1,
                'navs_in_footer': 0,
                'navs_floating': 0,
                'main_inside_section': True,  # This is an error!
                'total_divs': 150,
                'total_semantic': 50,
                'div_ratio': 0.75,  # 75% divs - too high!
                'has_divitis': True
            }
        }
    },
    'semantic_elements': {
        'header': {'count': 1, 'present': True},
        'nav': {'count': 1, 'present': True},
        'main': {'count': 1, 'present': True},
        'footer': {'count': 1, 'present': True},
        'article': {'count': 0, 'present': False},
        'section': {'count': 3, 'present': True},
        'aside': {'count': 0, 'present': False},
        'summary': {
            'total_semantic_elements': 6,
            'types_used': 4,
            'has_basic_structure': True
        }
    },
    'links': {'all_links': [], 'total_count': 0},
    'text_corpus': {
        'total_words': 500,
        'header_text': 'Test Header',
        'has_bolivia_service_text': False
    }
}

# Test data for a well-structured website
test_data_good = {
    'metadata': test_data['metadata'],
    'structure': {
        'has_html5_doctype': True,
        'doctype_text': 'html',
        'has_utf8_charset': True,
        'charset_declared': 'utf-8',
        'obsolete_elements': [],
        'obsolete_attributes': [],
        'has_obsolete_code': False,
        'has_html': True,
        'has_head': True,
        'has_body': True,
        'document_hierarchy': {
            'hierarchy': [],
            'structure_analysis': {
                'header_count': 1,
                'main_count': 1,
                'footer_count': 1,
                'nav_count': 1,
                'navs_in_header': 1,
                'navs_in_footer': 0,
                'navs_floating': 0,
                'main_inside_section': False,  # Correct!
                'total_divs': 30,
                'total_semantic': 70,
                'div_ratio': 0.30,  # Only 30% divs - good!
                'has_divitis': False
            }
        }
    },
    'semantic_elements': {
        'header': {'count': 1, 'present': True},
        'nav': {'count': 1, 'present': True},
        'main': {'count': 1, 'present': True},
        'footer': {'count': 1, 'present': True},
        'article': {'count': 5, 'present': True},
        'section': {'count': 3, 'present': True},
        'aside': {'count': 1, 'present': True},
        'summary': {
            'total_semantic_elements': 12,
            'types_used': 7,
            'has_basic_structure': True
        }
    },
    'links': test_data['links'],
    'text_corpus': test_data['text_corpus']
}

def test_sem03():
    evaluator = EvaluadorSemanticaTecnica()

    print("\n" + "="*80)
    print("TEST 1: Website with structural issues (BAD STRUCTURE)")
    print("="*80)

    result_bad = evaluator._evaluar_sem03(
        test_data['semantic_elements'],
        test_data['structure']
    )

    print(f"\nStatus: {result_bad.status}")
    print(f"Score: {result_bad.score}/{result_bad.max_score}")
    print(f"Percentage: {result_bad.details['percentage']}%")
    print(f"\nIssues found ({len(result_bad.details['issues'])}):")
    for issue in result_bad.details['issues']:
        print(f"  - {issue}")
    print(f"\nRecommendations ({len(result_bad.details['recommendations'])}):")
    for rec in result_bad.details['recommendations']:
        print(f"  - {rec}")

    print("\n" + "="*80)
    print("TEST 2: Website with good structure (GOOD STRUCTURE)")
    print("="*80)

    result_good = evaluator._evaluar_sem03(
        test_data_good['semantic_elements'],
        test_data_good['structure']
    )

    print(f"\nStatus: {result_good.status}")
    print(f"Score: {result_good.score}/{result_good.max_score}")
    print(f"Percentage: {result_good.details['percentage']}%")
    print(f"\nIssues found ({len(result_good.details['issues'])}):")
    for issue in result_good.details['issues']:
        print(f"  - {issue}")
    print(f"\nRecommendations ({len(result_good.details['recommendations'])}):")
    for rec in result_good.details['recommendations']:
        print(f"  - {rec}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Bad structure score: {result_bad.score}/{result_bad.max_score} ({result_bad.details['percentage']}%)")
    print(f"Good structure score: {result_good.score}/{result_good.max_score} ({result_good.details['percentage']}%)")
    print(f"\nImprovement detection working: {result_good.score > result_bad.score}")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_sem03()
