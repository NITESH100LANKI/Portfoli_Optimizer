# Portfolio Optimizer

A modular Python application designed to load stock data and compute optimized portfolio weights.

## Project Structure
- `app/`: Source code.
  - `data_loader.py`: Handles CSV data loading.
  - `optimizer.py`: Contains weight computation logic.
  - `services/`: Service layer orchestration.
  - `utils/`: Common utilities like logging.
- `data/`: Sample data storage.
- `tests/`: Unit tests for the application.

## Prerequisites
- Python 3.12+
- Pandas, NumPy, Pytest (install via `requirements.txt`)

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### CLI Mode
Run the application locally using:
```bash
python -m app.main
```

### API Mode
Start the REST API server:
```bash
uvicorn app.api:app --reload
```

### Research Dashboard (NEW)
Start the Streamlit research suite:
```bash
streamlit run app/streamlit_app.py
```
This dashboard provides:
- Top 50 Indian Stock Rankings (Nifty 50).
- Automated Research Watchlist.
- **AI Research Assistant**: Chat with an expert system for diagnostic stock reports.
- Technical Indicator Analysis (RSI, MACD, Support/Resistance).
- News Sentiment Scoring.

## Testing
Run unit tests with:
```bash
pytest
```
