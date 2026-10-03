from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class ConsistencyChecker:

    def __init__(self, threshold=0.50):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.threshold = threshold

    def semantic_similarity(self, text1, text2):
        embeddings = self.model.encode([text1, text2])
        similarity = cosine_similarity(
            [embeddings[0]],
            [embeddings[1]]
        )[0][0]
        return float(similarity)

    def _version_tuple(self, version_str):
        return tuple(int(x) for x in version_str.split("."))

    def _version_in_range(self, version, start, end):
        v = self._version_tuple(version)
        return self._version_tuple(start) <= v <= self._version_tuple(end)

    def _action_polarity_of(self, constraint):
        return constraint.get("action_polarity")

    def check(self, evidence_constraints, answer_constraints):

        tau = self.threshold

        # NEGATION
        for evidence in evidence_constraints:
            if evidence["type"] != "NEGATION":
                continue
            for answer in answer_constraints:
                if answer["type"] != "NEGATION":
                    continue

                subject_similarity = self.semantic_similarity(evidence["subject"], answer["subject"])
                action_similarity = self.semantic_similarity(evidence["action"], answer["action"])

                same_subject = subject_similarity >= tau
                same_action = action_similarity >= tau
                opposite_polarity = evidence["polarity"] != answer["polarity"]

                if same_subject and same_action and opposite_polarity:
                    return {
                        "contradiction": True, "type": "NEGATION CONTRADICTION", "risk": "HIGH",
                        "subject_similarity": subject_similarity, "action_similarity": action_similarity,
                        "evidence_constraint": evidence["text"], "answer_constraint": answer["text"],
                        "evidence_polarity": evidence["polarity"], "answer_polarity": answer["polarity"]
                    }

        # PREREQUISITE
        for evidence in evidence_constraints:
            if evidence["type"] != "PREREQUISITE":
                continue
            for answer in answer_constraints:
                if answer["type"] != "PREREQUISITE":
                    continue

                requirement_similarity = self.semantic_similarity(evidence["requirement"], answer["requirement"])
                same_requirement = requirement_similarity >= tau
                answer_is_negative = answer.get("polarity") == "NEGATIVE"

                if same_requirement and answer_is_negative:
                    return {
                        "contradiction": True, "type": "PREREQUISITE CONTRADICTION", "risk": "HIGH",
                        "requirement_similarity": requirement_similarity,
                        "evidence_constraint": evidence["text"], "answer_constraint": answer["text"]
                    }

        # CONDITION
        for evidence in evidence_constraints:
            if evidence["type"] != "CONDITION":
                continue
            for answer in answer_constraints:
                if answer["type"] != "CONDITION":
                    continue

                action_similarity = self.semantic_similarity(evidence["action"], answer["action"])
                condition_similarity = self.semantic_similarity(evidence["condition"], answer["condition"])

                same_action = action_similarity >= tau
                same_condition = condition_similarity >= tau
                opposite_polarity = evidence["polarity"] != answer["polarity"]

                if same_action and same_condition and opposite_polarity:
                    return {
                        "contradiction": True, "type": "CONDITION CONTRADICTION", "risk": "HIGH",
                        "action_similarity": action_similarity, "condition_similarity": condition_similarity,
                        "evidence_constraint": evidence["text"], "answer_constraint": answer["text"],
                        "evidence_polarity": evidence["polarity"], "answer_polarity": answer["polarity"]
                    }

                if "action_stripped" in evidence and "action_stripped" in answer:
                    stripped_similarity = self.semantic_similarity(
                        evidence["action_stripped"], answer["action_stripped"]
                    )
                    same_core_action = stripped_similarity >= tau
                    opposite_action_polarity = evidence["action_polarity"] != answer["action_polarity"]

                    if same_core_action and opposite_action_polarity:
                        return {
                            "contradiction": True, "type": "CONDITION CONTRADICTION (action flip)", "risk": "HIGH",
                            "action_stripped_similarity": stripped_similarity,
                            "evidence_constraint": evidence["text"], "answer_constraint": answer["text"],
                            "evidence_action_polarity": evidence["action_polarity"],
                            "answer_action_polarity": answer["action_polarity"]
                        }

                if condition_similarity >= tau and self._has_opposite_meaning(evidence["action"], answer["action"]):
                    return {
                        "contradiction": True, "type": "CONDITION CONTRADICTION (antonym)", "risk": "HIGH",
                        "condition_similarity": condition_similarity,
                        "evidence_constraint": evidence["text"], "answer_constraint": answer["text"]
                    }

        # VERSION
        for evidence in evidence_constraints:
            if evidence["type"] != "VERSION":
                continue
            for answer in answer_constraints:
                if answer["type"] != "VERSION":
                    continue
                answer_version = answer.get("version")
                if answer_version is None:
                    continue

                if evidence.get("status") == "PATCHED" and "version" in evidence:
                    if evidence["version"] == answer_version and answer.get("status") == "VULNERABLE":
                        return {
                            "contradiction": True, "type": "VERSION CONTRADICTION", "risk": "HIGH",
                            "evidence_constraint": evidence["text"], "answer_constraint": answer["text"],
                            "evidence_status": evidence["status"], "answer_status": answer["status"]
                        }

                if evidence.get("status") == "AFFECTED" and "start_version" in evidence:
                    in_range = self._version_in_range(answer_version, evidence["start_version"], evidence["end_version"])
                    if in_range and answer.get("status") == "PATCHED":
                        return {
                            "contradiction": True, "type": "VERSION CONTRADICTION", "risk": "HIGH",
                            "evidence_constraint": evidence["text"], "answer_constraint": answer["text"],
                            "evidence_status": evidence["status"], "answer_status": answer["status"]
                        }

        return {"contradiction": False, "type": "NO CONTRADICTION", "risk": "LOW"}

    def _has_opposite_meaning(self, text1, text2):
        antonym_pairs = [
            ("expire", "valid"), ("expire", "stays"),
            ("stop", "continue"), ("stop", "keep"), ("stop", "keeps"),
            ("block", "allow"), ("blocked", "allowed"),
            ("deny", "permit"), ("denied", "permitted"),
            ("disable", "enable"), ("disabled", "enabled"),
            ("lock", "unlock"), ("locked", "unlocked"),
            ("fail", "succeed"), ("reject", "accept"), ("rejected", "accepted"),
        ]
        t1, t2 = text1.lower(), text2.lower()
        for a, b in antonym_pairs:
            if (a in t1 and b in t2) or (b in t1 and a in t2):
                return True
        return False