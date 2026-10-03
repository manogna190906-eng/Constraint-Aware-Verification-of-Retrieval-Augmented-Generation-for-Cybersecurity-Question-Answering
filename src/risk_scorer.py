class RiskScorer:

    # How severe each contradiction type is, in principle,
    # independent of how confident the match was.
    TYPE_SEVERITY = {
        "NEGATION CONTRADICTION": 0.90,
        "PREREQUISITE CONTRADICTION": 0.85,
        "CONDITION CONTRADICTION": 0.85,
        "VERSION CONTRADICTION": 0.90,
        "NO CONTRADICTION": 0.0
    }

    def score(self, result):
        """
        Takes the dict returned by ConsistencyChecker.check()
        and returns a risk score between 0.0 and 1.0,
        plus a LOW/MEDIUM/HIGH bucket.
        """

        contradiction_type = result["type"]

        base_severity = self.TYPE_SEVERITY.get(
            contradiction_type,
            0.0
        )

        if not result["contradiction"]:
            return {
                "risk_score": 0.0,
                "risk_level": "LOW",
                "base_severity": base_severity,
                "confidence": 0.0
            }

        # Collect whatever similarity scores this result has.
        # Different contradiction types store different keys,
        # so we gather all of them that are present.
        similarity_keys = [
            "subject_similarity",
            "action_similarity",
            "condition_similarity",
            "requirement_similarity"
        ]

        similarities = [
            result[key]
            for key in similarity_keys
            if key in result
        ]

        if similarities:
            confidence = sum(similarities) / len(similarities)
        else:
            # VERSION contradictions currently don't carry a
            # similarity score (they're exact version-number
            # matches), so treat an exact match as full confidence.
            confidence = 1.0

        risk_score = base_severity * confidence

        if risk_score >= 0.60:
            risk_level = "HIGH"
        elif risk_score >= 0.30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "base_severity": base_severity,
            "confidence": round(confidence, 3)
        }