Get-ChildItem "C:\Users\Lopez\OneDrive\Escritorio\TradeupSPY\OK" -Filter *.csv | ForEach-Object {
  python -m tradeup.cli `
    --contract $_.FullName `
    --catalog "data/skins_fixed.csv" `
    --fetch-prices `
    --json
  Start-Sleep -Seconds 1.5
}



python scripts/evaluate_all_contracts.py --contracts-dir "C:\Users\Lopez\OneDrive\Escritorio\TradeupSPY\OK" --catalog "data/skins_fixed.csv" --extra-cli-flags="--fetch-prices" --sleep 1.5 --retries 6 --backoff 5 --workers 1