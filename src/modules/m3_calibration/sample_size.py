import math

Z_95 = 1.96


def wilson_interval(correct: int, total: int) -> tuple[float, float]:
    p = correct / total
    denominator = 1 + Z_95**2 / total
    center = (p + Z_95**2 / (2 * total)) / denominator
    margin = Z_95 * math.sqrt(p * (1 - p) / total + Z_95**2 / (4 * total**2)) / denominator
    return center - margin, center + margin


def main() -> None:
    print("Измерили точность 0.80. Где на самом деле точность модели (95%)?")
    for total in (20, 58, 100, 200, 400, 1000):
        low, high = wilson_interval(round(total * 0.8), total)
        print(f"  {total:5d} примеров: от {low:.2f} до {high:.2f}")


if __name__ == "__main__":
    main()
