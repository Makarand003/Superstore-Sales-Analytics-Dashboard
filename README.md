# Superstore Sales Analytics Dashboard

This project turns the Kaggle Superstore sales data into a small analytics product: a Streamlit dashboard for business exploration and a daily sales forecasting pipeline.

I kept the scope practical. The copy of the dataset in this project has sales, order, customer, product, geography, and shipping fields, but it does not include `Profit`, `Quantity`, or `Discount`. Because of that, the dashboard focuses on sales performance rather than pretending to analyze margins or discount behavior.

## Objectives

- Clean and prepare four years of Superstore order data.
- Explore sales by time, region, category, segment, and product.
- Build a daily sales forecast using a SARIMAX model.
- Save reusable processed data and a model artifact.
- Provide an interactive dashboard that a stakeholder can filter without opening a notebook.

## Dataset

Source: [Kaggle - Superstore Sales Forecasting](https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting)

The raw file has 9,800 rows and 18 columns. Important fields include order dates, ship dates, ship mode, customer details, segment, geography, product hierarchy, and sales amount.

## Project Structure

```text
.
├── data/
│   ├── raw/train.csv
│   └── processed/
├── models/
├── reports/
├── dashboard.py
├── train.py
├── Superstore_Analytics.ipynb
├── HELP_GUIDE.md
├── README.md
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If Prophet is slow to install on your machine, the rest of the project still uses SARIMAX from `statsmodels`. I included Prophet because it is useful for a next iteration and was part of the requested stack.

## Run the Forecasting Pipeline

```bash
python train.py --data-path data/raw/train.csv
```

This writes:

- `data/processed/cleaned_superstore.csv`
- `data/processed/daily_sales.csv`
- `models/sales_forecast_sarimax.joblib`

## Run the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard includes KPI cards, date/category/region/segment filters, sales trend charts, top products, forecast output, and a filtered CSV download.

## Key Insights

The highest-value views in this dataset are the basic but useful ones: sales over time, category contribution, regional concentration, and the products driving the most revenue. I found the monthly trend more readable than daily sales because daily order volume is noisy and has many low-sales days.

One caveat: because the dataset does not include profit, quantity, or discount in this file, it cannot answer margin or promotion questions. In a real business setting, I would ask for those fields before making pricing or profitability recommendations.

## Forecasting Approach

I used a SARIMAX model with weekly seasonality on daily aggregated sales. It is not the flashiest model, but it is easy to explain, quick to train, and reasonable for a first forecasting baseline. The last 30 days are held out for evaluation using MAE and RMSE.

Next time I would compare SARIMAX with Prophet and a tree-based model using lag features. I would also add holiday/event variables if the business had that context.

## Deployment Notes

For a lightweight deployment, Streamlit Community Cloud works well:

1. Push this project to GitHub.
2. Set `dashboard.py` as the app entry point.
3. Keep `data/raw/train.csv` in the repo or replace it with a secure data source.
4. Run `python train.py` before deployment, or commit the model artifact if allowed.

For a production setup, I would separate model training from dashboard serving and schedule the training job separately.
