from dataclasses import dataclass


@dataclass(frozen=True)
class Bin:
    low: float
    high: float
    count: int
    mean_probability: float
    observed: float


def reliability_bins(
    probabilities: list[float], outcomes: list[bool], n_bins: int = 5
) -> list[Bin]:
    bins = []
    for index in range(n_bins):
        low, high = index / n_bins, (index + 1) / n_bins
        inside = [
            (p, y)
            for p, y in zip(probabilities, outcomes, strict=True)
            if low <= p < high or (index == n_bins - 1 and p == 1.0)
        ]
        if not inside:
            continue
        bins.append(
            Bin(
                low=low,
                high=high,
                count=len(inside),
                mean_probability=sum(p for p, _ in inside) / len(inside),
                observed=sum(y for _, y in inside) / len(inside),
            )
        )
    return bins


def expected_calibration_error(
    probabilities: list[float], outcomes: list[bool], n_bins: int = 5
) -> float:
    total = len(probabilities)
    return sum(
        b.count / total * abs(b.mean_probability - b.observed)
        for b in reliability_bins(probabilities, outcomes, n_bins)
    )


def brier_score(probabilities: list[float], outcomes: list[bool]) -> float:
    pairs = zip(probabilities, outcomes, strict=True)
    return sum((p - y) ** 2 for p, y in pairs) / len(probabilities)


def print_reliability(title: str, probabilities: list[float], outcomes: list[bool]) -> None:
    print(title)
    print("  bin        n   mean p   observed")
    for b in reliability_bins(probabilities, outcomes):
        bar = "#" * round(b.observed * 20)
        print(
            f"  {b.low:.1f}-{b.high:.1f}  {b.count:3d}   {b.mean_probability:.2f}     "
            f"{b.observed:.2f}  {bar}"
        )
    ece = expected_calibration_error(probabilities, outcomes)
    brier = brier_score(probabilities, outcomes)
    print(f"  ECE: {ece:.3f}, Brier: {brier:.3f}")
