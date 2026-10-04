from app.brokers.alpaca import AlpacaClient, AlpacaError


def main():
    try:
        client = AlpacaClient()
        result = client.health_check()

        print("=== TRADING APP v2.0 / ALPACA ===")
        print("Connected:", result["connected"])
        print("Paper mode:", result["paper"])
        print("Account status:", result["status"])
        print("Trading blocked:", result["trading_blocked"])
        print("Account blocked:", result["account_blocked"])
        print("Buying power: $" + str(result["buying_power"]))
        print("RESULT: PASS")

    except AlpacaError as exc:
        print("RESULT: FAIL")
        print(exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
