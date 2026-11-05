import json

RESPONSE = """
{
  "model": "jev-1.13.0",
  "answers": {
    "department": {
      "type": "choice",
      "choice": "technical",
      "confidence": 1.0,
      "probabilities": {"technical": 1.0, "billing": 0.0, "sales": 0.0}
    },
    "frustration": {
      "type": "score",
      "score": 0.67,
      "confidence": 0.5,
      "legend": {"0": "Calm, just stating facts", "1": "Frustrated but civil", "2": "Very angry, strong language"},
      "probabilities": {"0": 0.33, "1": 0.67, "2": 0.0}
    },
    "is_urgent": {"type": "noul", "noul": 0.99}
  },
  "usage": {"input_tokens": 428, "output_tokens": 73}
}
"""


def main() -> None:
    answers = json.loads(RESPONSE)["answers"]

    department = answers["department"]
    print(f"department: {department['choice']} (confidence {department['confidence']})")

    frustration = answers["frustration"]
    print(f"frustration: {frustration['score']} (confidence {frustration['confidence']})")

    print(f"is_urgent: вероятность да = {answers['is_urgent']['noul']}")


if __name__ == "__main__":
    main()
