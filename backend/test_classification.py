from classification import parse_company_and_role

test_cases = [
    {
        "subject": "Internship - Software Engineering at ASML: Thank you for applying",
        "email": "no-reply@myworkday.com",
        "expected_role": "Software Engineering",
        "expected_company": "ASML" 
    },
    {
        "subject": "Thank you for your application",
        "email": "careers@zebra.com",
        "expected_role": None,
        "expected_company": "zebra"
    },
    {
        "subject": "Application received: Software Engineer at Google",
        "email": "google-noreply@gmail.com",
        "expected_role": "Software Engineer",
        "expected_company": "Google"
    },
    {
        "subject": "Thank you for applying to the Frontend Developer position",
        "email": "jobs@startup.com",
        "expected_role": "Frontend Developer",
        "expected_company": "startup"
    }
]

print("Running tests...")
for i, case in enumerate(test_cases):
    print(f"\nCase {i+1}: '{case['subject']}' from {case['email']}")
    result = parse_company_and_role(case["subject"], case["email"])
    print(f"  Got: Role='{result['role']}', Company='{result['company']}'")
    
    # Heuristic checks
    if case.get("expected_company") and case["expected_company"].lower() not in (result["company"] or "").lower():
         print(f"  [WARNING] Company mismatch. Expected something like {case['expected_company']}")
    
    if case.get("expected_role") and case["expected_role"].lower() not in (result["role"] or "").lower():
         print(f"  [WARNING] Role mismatch. Expected something like {case['expected_role']}")
