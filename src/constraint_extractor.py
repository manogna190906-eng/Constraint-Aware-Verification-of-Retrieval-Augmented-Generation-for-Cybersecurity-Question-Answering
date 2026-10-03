class ConstraintExtractor:

    def _clean_sentence(self, sentence_lower):
        """
        Strip leading discourse markers like 'Yes,' / 'No,'
        that add noise without adding meaning, and normalize
        a few common phrasings to the words our regex/keyword
        matching already understands.
        """

        import re

        sentence_lower = re.sub(r"^(yes|no)[,\.]?\s*", "", sentence_lower)

        sentence_lower = sentence_lower.replace("capable of", "can")
        sentence_lower = sentence_lower.replace("is able to", "can")
        sentence_lower = sentence_lower.replace("is unable to", "cannot")
        sentence_lower = sentence_lower.replace("not able to", "cannot")

        return sentence_lower
    def extract_negation(self, text):
        constraints = []

        sentences = text.split(".")

        adjective_pairs = [
            ("unreachable", "reachable"),
            ("inaccessible", "accessible"),
            ("unavailable", "available"),
            ("unauthorized", "authorized"),
            ("invalid", "valid"),
            ("unable", "able"),
        ]

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_lower = self._clean_sentence(sentence.lower())

            if " cannot " in f" {sentence_lower} ":
                parts = sentence_lower.split("cannot", 1)

                subject = parts[0].strip()
                action = parts[1].strip()

                constraints.append({
                    "type": "NEGATION",
                    "subject": subject,
                    "action": action,
                    "polarity": "NEGATIVE",
                    "text": sentence
                })

            elif " can " in f" {sentence_lower} ":
                parts = sentence_lower.split("can", 1)

                subject = parts[0].strip()
                action = parts[1].strip()

                constraints.append({
                    "type": "NEGATION",
                    "subject": subject,
                    "action": action,
                    "polarity": "POSITIVE",
                    "text": sentence
                })

            else:
                # Fallback: adjectival negation not caught by can/cannot,
                # e.g. "reachable" / "unreachable", "valid" / "invalid"
                matched = False
                for neg_word, pos_word in adjective_pairs:
                    if neg_word in sentence_lower:
                        parts = sentence_lower.split(neg_word, 1)
                        constraints.append({
                            "type": "NEGATION",
                            "subject": parts[0].strip(),
                            "action": (neg_word + " " + parts[1]).strip(),
                            "polarity": "NEGATIVE",
                            "text": sentence
                        })
                        matched = True
                        break

                if not matched:
                    for neg_word, pos_word in adjective_pairs:
                        if pos_word in sentence_lower:
                            parts = sentence_lower.split(pos_word, 1)
                            constraints.append({
                                "type": "NEGATION",
                                "subject": parts[0].strip(),
                                "action": (pos_word + " " + parts[1]).strip(),
                                "polarity": "POSITIVE",
                                "text": sentence
                            })
                            break

        return constraints

    def extract_prerequisites(self, text):

        import re

        constraints = []

        sentences = text.split(".")

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_lower = self._clean_sentence(sentence.lower())

            if "requires " in sentence_lower:

                parts = sentence_lower.split("requires ", 1)

                action = parts[0].strip()
                requirement = parts[1].strip()

                constraints.append({
                    "type": "PREREQUISITE",
                    "action": action,
                    "requirement": requirement,
                    "text": sentence
                })
            elif "without " in sentence_lower:

                parts = sentence_lower.split("without ", 1)

                action = parts[0].strip()
                requirement = parts[1].strip()

                # "cannot X without Y" is a double negative meaning
                # "Y is required" — NOT a negative prerequisite.
                # Only treat as NEGATIVE when "without" stands alone,
                # without an earlier "cannot"/"can not" in the same clause.
                if "cannot" in action or "can not" in action:
                    constraints.append({
                        "type": "PREREQUISITE",
                        "action": action,
                        "requirement": requirement,
                        "text": sentence
                    })
                else:
                    constraints.append({
                        "type": "PREREQUISITE",
                        "action": action,
                        "requirement": requirement,
                        "polarity": "NEGATIVE",
                        "text": sentence
                    })

            else:
                match = re.search(
                    r"no\s+(.+?)\s+(?:needed|required)",
                    sentence_lower
                )

                if match:

                    requirement = match.group(1).strip()

                    constraints.append({
                        "type": "PREREQUISITE",
                        "action": sentence_lower,
                        "requirement": requirement,
                        "polarity": "NEGATIVE",
                        "text": sentence
                    })

        return constraints

    def _action_polarity(self, action_text):
        negation_markers = [" does not ", " do not ", " cannot ", " can not ",
                             " never ", " won't ", " will not ", " isn't ",
                             " is not ", " doesn't "]
        padded = f" {action_text} "
        for marker in negation_markers:
            if marker in padded:
                return "NEGATIVE"
        return "POSITIVE"

    def _strip_negation(self, action_text):
        padded = f" {action_text} "
        replacements = {
            " does not ": " ", " do not ": " ", " cannot ": " ", " can not ": " ",
            " never ": " ", " won't ": " will ", " will not ": " will ",
            " isn't ": " is ", " is not ": " is ", " doesn't ": " "
        }
        for marker, repl in replacements.items():
            padded = padded.replace(marker, repl)
        return padded.strip()

    def extract_conditions(self, text):

        constraints = []
        sentences = text.split(".")

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_lower = self._clean_sentence(sentence.lower())

            if "only when " in sentence_lower:
                parts = sentence_lower.split("only when ", 1)
                action = parts[0].strip()
                constraints.append({
                    "type": "CONDITION", "action": action, "condition": parts[1].strip(),
                    "polarity": "REQUIRED",
                    "action_polarity": self._action_polarity(action),
                    "action_stripped": self._strip_negation(action),
                    "text": sentence
                })
            elif "except when " in sentence_lower:
                parts = sentence_lower.split("except when ", 1)
                action = parts[0].strip()
                constraints.append({
                    "type": "CONDITION", "action": action, "condition": parts[1].strip(),
                    "polarity": "REQUIRED",
                    "action_polarity": self._action_polarity(action),
                    "action_stripped": self._strip_negation(action),
                    "text": sentence
                })
            elif "unless " in sentence_lower:
                parts = sentence_lower.split("unless ", 1)
                action = parts[0].strip()
                constraints.append({
                    "type": "CONDITION", "action": action, "condition": parts[1].strip(),
                    "polarity": "REQUIRED",
                    "action_polarity": self._action_polarity(action),
                    "action_stripped": self._strip_negation(action),
                    "text": sentence
                })
            elif "even when " in sentence_lower:
                parts = sentence_lower.split("even when ", 1)
                action = parts[0].strip()
                constraints.append({
                    "type": "CONDITION", "action": action, "condition": parts[1].strip(),
                    "polarity": "NEGATIVE",
                    "action_polarity": self._action_polarity(action),
                    "action_stripped": self._strip_negation(action),
                    "text": sentence
                })
            elif "regardless of " in sentence_lower:
                parts = sentence_lower.split("regardless of ", 1)
                action = parts[0].strip()
                constraints.append({
                    "type": "CONDITION", "action": action, "condition": parts[1].strip(),
                    "polarity": "NEGATIVE",
                    "action_polarity": self._action_polarity(action),
                    "action_stripped": self._strip_negation(action),
                    "text": sentence
                })

        return constraints

    def extract_versions(self, text):

        import re

        constraints = []

        sentences = re.split(r"\.(?!\d)", text)

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            sentence_lower = sentence.lower()

            match = re.search(
                r"versions?\s+(\d+(?:\.\d+)*)\s+through\s+(\d+(?:\.\d+)*)",
                sentence_lower
            )
            if match:
                constraints.append({
                    "type": "VERSION",
                    "start_version": match.group(1),
                    "end_version": match.group(2),
                    "status": "AFFECTED",
                    "text": sentence
                })

            match = re.search(
                r"version\s+(\d+(?:\.\d+)*)\s+contains\s+the\s+security\s+patch",
                sentence_lower
            )
            if match:
                constraints.append({
                    "type": "VERSION",
                    "version": match.group(1),
                    "status": "PATCHED",
                    "text": sentence
                })

            match = re.search(
                r"version\s+(\d+(?:\.\d+)*)\s+resolves\s+the\s+issue",
                sentence_lower
            )
            if match:
                constraints.append({
                    "type": "VERSION",
                    "version": match.group(1),
                    "status": "PATCHED",
                    "text": sentence
                })

            match = re.search(
                r"version\s+(\d+(?:\.\d+)*)\s+is\s+vulnerable",
                sentence_lower
            )
            if match:
                constraints.append({
                    "type": "VERSION",
                    "version": match.group(1),
                    "status": "VULNERABLE",
                    "text": sentence
                })

            match = re.search(
                r"version\s+(\d+(?:\.\d+)*)\s+is\s+still\s+affected",
                sentence_lower
            )
            if match:
                constraints.append({
                    "type": "VERSION",
                    "version": match.group(1),
                    "status": "VULNERABLE",
                    "text": sentence
                })

        return constraints