# Help Guide

This guide explains how the project works from raw data to dashboard and forecast. I wrote it as the kind of project note I would want to hand to another analyst joining the work later.

## Workflow

1. `data/raw/train.csv` stores the original Superstore CSV.
2. `train.py` loads the raw file, cleans dates and postal codes, aggregates daily sales, trains a SARIMAX model, and saves outputs.
3. `Superstore_Analytics.ipynb` walks through the same process interactively with charts and notes.
4. `dashboard.py` reads the cleaned logic directly from `train.py`, applies user filters, shows KPIs and charts, and loads the saved forecast model.

I reused functions from `train.py` in the dashboard because it keeps the cleaning rules in one place. In my experience, small analytics projects get messy fast when the notebook, app, and training script each have their own slightly different version of "clean data".

## Data Notes

The user story mentions profit, quantity, and discount, but the provided CSV has 18 columns and does not include those fields. I handled that as a data limitation. The dashboard therefore avoids profit KPIs and focuses on revenue, orders, customers, product mix, and forecasted sales.

## `train.py` Explained

Lines 1-10 import the standard libraries and modeling tools. `joblib` is used for model persistence, `pandas` and `numpy` handle data preparation, `sklearn.metrics` evaluates the forecast, and `SARIMAX` provides the time series model.

Line 13 defines `DATE_COLUMNS`. Keeping this list near the top makes it easier to update if another date field is added later.

Lines 16-18 define `load_data`. It reads the CSV with `latin1` encoding because this Kaggle file can contain product names that do not always behave cleanly with stricter encodings.

Lines 21-32 define `clean_data`. The function copies the input dataframe, converts `Order Date` and `Ship Date`, fills missing postal codes, creates `Ship Delay Days`, removes rows without usable dates or sales, and filters out negative sales. I chose not to drop rows just because postal code is missing because geography is still usable at city/state/region level.

Lines 35-51 define `build_daily_sales`. Orders are grouped by `Order Date`, sales are summed, and order counts are calculated. The function then reindexes the result to a complete daily date range. This part matters for forecasting because time series models behave better when the frequency is explicit.

Lines 54-76 define `train_forecast_model`. The last 30 days are used as a simple holdout set. SARIMAX is configured with a basic `(1, 1, 1)` trend component and weekly seasonal terms. This is a baseline, not a final production model, but it is explainable and fast enough for this dataset.

Lines 68-72 calculate MAE and RMSE. MAE is easier to explain to stakeholders because it is in dollars. RMSE is more sensitive to big misses, which is useful here because daily sales can spike.

Lines 79-95 define `save_outputs`. It creates output folders if needed, saves cleaned row-level data, saves daily aggregated data, and writes the fitted model plus metrics into `models/sales_forecast_sarimax.joblib`.

Lines 98-116 define `main`. It parses command-line arguments, runs the whole pipeline, saves outputs, and prints the key results. This makes the file useful from both the terminal and as an importable module.

Line 119 runs `main` only when the script is executed directly. That is why `dashboard.py` can import the helper functions without accidentally retraining the model.

## `dashboard.py` Explained

Lines 1-9 import libraries and reuse helper functions from `train.py`. This is the small design decision that keeps the app consistent with the training pipeline.

Lines 12-13 define paths for the raw dataset and trained model. They are relative paths so the app works when run from the project root.

Lines 16-18 define `get_clean_data`, cached with Streamlit. The cache keeps the app responsive when filters change because the CSV does not need to be re-read each time.

Lines 21-31 define `apply_filters`. It filters by region, category, segment, and order date range. I kept this as a separate function because filter bugs are easier to test and fix when they are isolated.

Lines 34-42 define `forecast_next_days`. If the model exists, it loads the saved SARIMAX artifact and forecasts the selected horizon. If not, the dashboard returns an empty dataframe and shows a friendly warning.

Lines 45-53 configure the Streamlit page and stop early if the raw dataset is missing.

Lines 55-70 build the sidebar. The user can filter by region, category, segment, date range, and forecast horizon. The defaults show the full dataset, which is usually the least surprising first view.

Lines 72-75 validate the date picker. Streamlit can temporarily return a single date while the user is interacting, so this guard prevents confusing errors.

Lines 77-87 calculate the KPI values: total sales, unique orders, unique customers, and average order value.

Lines 89-92 render the KPI cards. These are the quick executive summary before the user gets into the charts.

Lines 94-96 handle the empty-filter case.

Lines 98-106 prepare daily and monthly sales. Monthly sales are used for the trend chart because the daily line is visually noisy.

Lines 108-120 create the monthly sales and region charts.

Lines 122-131 create the category and segment charts.

Lines 133-143 show the top 10 products by sales. This is often where a stakeholder starts asking better follow-up questions.

Lines 145-153 show the forecast chart if the trained model exists.

Lines 155-156 create a downloadable filtered CSV. I found this helpful because dashboard users often want to take the filtered slice into Excel for a quick check.

## Notebook Guide

The notebook follows the same structure as the production script:

- Project framing and data limitation notes.
- Load the raw CSV from `data/raw/train.csv`.
- Inspect shape, data types, missing values, and sample rows.
- Clean dates, postal code, shipping delay, and sales values.
- Create monthly and grouped EDA views.
- Plot sales over time, region, category, segment, ship mode, and top products.
- Aggregate daily sales for forecasting.
- Train a SARIMAX model with a 30-day holdout.
- Evaluate using MAE and RMSE.
- Save the model with `joblib`.

The notebook is intentionally a little more conversational than the script. That is where I left the reasoning and caveats, while the script stays focused on repeatability.

## How Data Flows

Raw CSV enters through `data/raw/train.csv`. Cleaning converts date strings, fills missing postal codes, calculates shipping delay, and removes unusable rows. Cleaned order-level data supports dashboard filters and product/category views. Daily aggregated data supports forecasting. The trained model is saved in `models/`, and the dashboard reads it when showing future sales predictions.

## Extending the Project

Good next steps:

- Add profit, quantity, and discount if those columns become available.
- Compare SARIMAX with Prophet and lag-based machine learning models.
- Add holiday and promotion calendars.
- Add automated tests for cleaning and filtering functions.
- Move paths into a small config file if this grows beyond a portfolio project.

One thing I would change next time is the evaluation setup. A single 30-day holdout is okay for a baseline, but rolling backtests would give a more honest view of model stability.

## Common Commands

Install dependencies:

```bash
pip install -r requirements.txt
```

Train the model:

```bash
python train.py --data-path data/raw/train.csv
```

Run the dashboard:

```bash
streamlit run dashboard.py
```
