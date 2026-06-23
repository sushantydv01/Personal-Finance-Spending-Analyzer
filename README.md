# Personal Finance Spending Analyzer

A web-based dashboard and analysis tool to track, analyze, and visualize personal financial transactions. Built with Dash, Plotly, and Python.

## Project Structure

```text
finance-analyzer/
├── app.py              # Application entry point
├── config.py           # Configuration values (directories, settings)
├── requirements.txt    # Frozen environment dependencies
├── assets/
│   └── style.css       # Layout styles
├── components/
│   └── charts.py       # Reusable visualization charts
├── utils/
│   └── data_loader.py  # Data loading helpers
├── data/               # CSV/Excel transaction files
├── tests/
│   └── test_loader.py  # Unit tests
└── venv/               # Virtual environment
```

## Setup and Running

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sushantydv01/Personal-Finance-Spending-Analyzer.git
   cd Personal-Finance-Spending-Analyzer
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   # MacOS / Linux
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Dashboard:**
   ```bash
   python app.py
   ```
   Open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your web browser.
