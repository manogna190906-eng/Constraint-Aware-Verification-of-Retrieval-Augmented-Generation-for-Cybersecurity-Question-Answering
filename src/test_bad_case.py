from constraint_extractor import ConstraintExtractor
from consistency_checker import ConsistencyChecker


evidence = """
Successful exploitation of the vulnerability requires authenticated access.
Unauthenticated users cannot execute the attack.
"""

bad_answer = """
Yes. An unauthenticated user can execute the attack.
"""


print("EVIDENCE:")
print(evidence)

print("ANSWER:")
print(bad_answer)


# Step 1: Extract constraints
extractor = ConstraintExtractor()


print("\nDEBUG:")
print("ConstraintExtractor module:", ConstraintExtractor.__module__)

import constraint_extractor
import inspect

print("Loaded file:", constraint_extractor.__file__)
print("Has extract_versions:", hasattr(extractor, "extract_versions"))

print("\nACTUAL extract_versions CODE:")
print(inspect.getsource(ConstraintExtractor.extract_versions))

prerequisite_evidence = """
Successful exploitation of the vulnerability requires administrator privileges.
"""

bad_prerequisite_answer = """
The vulnerability can be exploited without administrator privileges.
"""

print("\nPREREQUISITE TEST:")
print(prerequisite_evidence)

print("\nBAD PREREQUISITE ANSWER:")
print(bad_prerequisite_answer)


prerequisites = extractor.extract_prerequisites(
    prerequisite_evidence
)

answer_prerequisites = extractor.extract_prerequisites(
    bad_prerequisite_answer
)


print("EXTRACTED EVIDENCE PREREQUISITE:")
print(prerequisites)

print("\nEXTRACTED ANSWER PREREQUISITE:")
print(answer_prerequisites)


evidence_constraints = extractor.extract_negation(evidence)
answer_constraints = extractor.extract_negation(bad_answer)


print("\nEXTRACTED EVIDENCE CONSTRAINT:")
print(evidence_constraints)

print("\nEXTRACTED ANSWER CONSTRAINT:")
print(answer_constraints)


condition_evidence = """
Remote exploitation is possible only when Feature A is enabled.
"""

bad_condition_answer = """
Remote exploitation is possible even when Feature A is disabled.
"""


print("\nCONDITION TEST:")
print(condition_evidence)

print("\nBAD CONDITION ANSWER:")
print(bad_condition_answer)


conditions = extractor.extract_conditions(
    condition_evidence
)

answer_conditions = extractor.extract_conditions(
    bad_condition_answer
)


print("EXTRACTED EVIDENCE CONDITION:")
print(conditions)

print("\nEXTRACTED ANSWER CONDITION:")
print(answer_conditions)


# Step 2: Check consistency
checker = ConsistencyChecker()


result = checker.check(
    evidence_constraints,
    answer_constraints
)

prerequisite_result = checker.check(
    prerequisites,
    answer_prerequisites
)

condition_result = checker.check(
    conditions,
    answer_conditions
)


print("\nPREREQUISITE RELIABILITY CHECK:")
print("Result:", prerequisite_result["type"])
print("Risk:", prerequisite_result["risk"])


if prerequisite_result["contradiction"]:

    print("\nWHY?")

    print(
        "Evidence:",
        prerequisite_result["evidence_constraint"]
    )

    print(
        "Answer:",
        prerequisite_result["answer_constraint"]
    )

    print(
        "Requirement similarity:",
        round(
            prerequisite_result["requirement_similarity"],
            3
        )
    )


print("\nCONDITION RELIABILITY CHECK:")
print("Result:", condition_result["type"])
print("Risk:", condition_result["risk"])


if condition_result["contradiction"]:

    print("\nWHY?")

    print(
        "Evidence:",
        condition_result["evidence_constraint"]
    )

    print(
        "Answer:",
        condition_result["answer_constraint"]
    )

    print(
        "Action similarity:",
        round(
            condition_result["action_similarity"],
            3
        )
    )

    print(
        "Condition similarity:",
        round(
            condition_result["condition_similarity"],
            3
        )
    )

    print(
        "Polarity:",
        condition_result["evidence_polarity"],
        "->",
        condition_result["answer_polarity"]
    )


print("\nRELIABILITY CHECK:")

print("Result:", result["type"])
print("Risk:", result["risk"])


if result["contradiction"]:

    print("\nWHY?")

    print(
        "Evidence:",
        result["evidence_constraint"]
    )

    print(
        "Answer:",
        result["answer_constraint"]
    )

    print(
        "Subject similarity:",
        round(
            result["subject_similarity"],
            3
        )
    )

    print(
        "Action similarity:",
        round(
            result["action_similarity"],
            3
        )
    )

    print(
        "Polarity:",
        result["evidence_polarity"],
        "->",
        result["answer_polarity"]
    )


# -----------------------------
# VERSION TEST
# -----------------------------

version_evidence = """
The vulnerability affects software versions 2.0 through 2.5.
Version 2.6 contains the security patch.
"""

bad_version_answer = """
Version 2.6 is vulnerable to the attack.
"""


print("\nVERSION TEST:")
print(version_evidence)

print("\nBAD VERSION ANSWER:")
print(bad_version_answer)


versions = extractor.extract_versions(
    version_evidence
)

answer_versions = extractor.extract_versions(
    bad_version_answer
)


print("EXTRACTED EVIDENCE VERSION:")
print(versions)

print("\nEXTRACTED ANSWER VERSION:")
print(answer_versions)


# -----------------------------
# VERSION RELIABILITY CHECK (NEW)
# -----------------------------

version_result = checker.check(
    versions,
    answer_versions
)

print("\nVERSION RELIABILITY CHECK:")
print("Result:", version_result["type"])
print("Risk:", version_result["risk"])

if version_result["contradiction"]:

    print("\nWHY?")

    print(
        "Evidence:",
        version_result["evidence_constraint"]
    )

    print(
        "Answer:",
        version_result["answer_constraint"]
    )

    print(
        "Status:",
        version_result["evidence_status"],
        "->",
        version_result["answer_status"]
    )