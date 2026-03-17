#!/usr/bin/env python3
import sys

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 pension.py <monthly_amount> <annual_interest_rate_%> <years>")
        sys.exit(1)

    try:
        monthly = float(sys.argv[1])
        annual_rate = float(sys.argv[2])
        years = int(sys.argv[3])
    except ValueError:
        print("Error: amount and interest must be numbers, years must be an integer.")
        sys.exit(1)

    monthly_rate = annual_rate / 100 / 12
    n = years * 12

    if monthly_rate == 0:
        total = monthly * n
    else:
        # Future value of annuity (end of period payments)
        total = monthly * ((1 + monthly_rate) ** n - 1) / monthly_rate

    invested = monthly * n
    interest_earned = total - invested

    print(f"\nMonthly contribution : {monthly:>12,.2f} €")
    print(f"Annual interest rate : {annual_rate:>12.2f} %")
    print(f"Duration             : {years:>12} years ({n} months)")
    print(f"{'─' * 42}")
    print(f"Total invested       : {invested:>12,.2f} €")
    print(f"Interest earned      : {interest_earned:>12,.2f} €")
    print(f"Final amount         : {total:>12,.2f} €")
    print(f"Multiplication factor: {total/invested:>12.2f}x")

if __name__ == "__main__":
    main()
