"""Прогноз погоды на 10 дней: те же формулы калибровки, что и для тикетов, но на числах, которые можно пересчитать руками."""

from src.ticketdesk.calibration import brier_score, expected_calibration_error, print_reliability

# Что синоптик написал: вероятность дождя в каждый из 10 дней.
FORECAST = [0.1, 0.1, 0.1, 0.1, 0.5, 0.5, 0.9, 0.9, 0.9, 0.9]
# Что было на самом деле: True, если дождь пошёл.
RAINED = [False, False, False, True, False, True, True, True, True, False]

# Второй синоптик каждый день пишет 0.5, ничего не различая.
SHRUG = [0.5] * 10


def main() -> None:
    print_reliability("forecaster", FORECAST, RAINED)
    print()
    print_reliability("always 50%", SHRUG, RAINED)
    print()
    for name, forecast in (("forecaster", FORECAST), ("always 50%", SHRUG)):
        ece = expected_calibration_error(forecast, RAINED)
        brier = brier_score(forecast, RAINED)
        print(f"{name}: ECE = {ece:.2f}, Brier = {brier:.3f}")


if __name__ == "__main__":
    main()
