from consistency_checker import ConsistencyChecker

checker = ConsistencyChecker()

pairs = [
    ("BM004", "identify encrypted payloads", "detect encrypted intrusion payloads using its signature database"),
    ("BM012", "direct network access to port 8443 on the target host", "any network access to the target host"),
    ("BM028", "root-level access to the server", "elevated access"),
    ("BM024-action", "the session token does not expire automatically", "the session token expires automatically after a few minutes"),
]

for case_id, text1, text2 in pairs:
    score = checker.semantic_similarity(text1, text2)
    print(f"{case_id}: {round(score, 3)}")
    print(f"   A: {text1}")
    print(f"   B: {text2}")
    print()