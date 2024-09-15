
# index_app

This is a multipage Streamlit app generated using a custom cookie cutter script.

## Project Structure

```
index_app/
│
├── app/
│   ├── main.py
│   ├── pages/
│   │   ├── page1.py
│   │   ├── page2.py
│   │   └── page3.py
│   ├── components/
│   │   └── sidebar.py
│   └── utils/
│       └── data_processing.py
│
├── data/
│   ├── raw/
│   └── processed/
│
├── tests/
│   └── test_data_processing.py
│
├── config/
│   └── config.yaml
│
├── requirements.txt
└── README.md
```

## Setup and Running

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the Streamlit app:
   ```
   streamlit run app/main.py
   ```

## Adding New Pages

To add a new page, create a new Python file in the `app/pages/` directory and update the `main.py` file to include the new page.

## Running Tests

To run the tests, use the following command:
```
python -m unittest discover tests
```
    