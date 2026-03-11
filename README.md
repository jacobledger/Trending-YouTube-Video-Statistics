# Trending YouTube Video Statistics

An exploratory data analysis and business report examining whether highly polarizing YouTube videos receive greater reach and engagement, using US and GB trending video datasets.

---

## Project Overview

This project was completed as a practice data analysis assignment. The analysis addresses five objectives:

1. Load and explore the US and GB trending YouTube video datasets
2. Create a likes-to-dislikes ratio column for each dataset
3. Calculate the average like-to-dislike ratio across all videos
4. Find the average number of views per video published in 2018
5. **Business report:** Evaluate whether the most polarizing videos get shared the most, and identify what other metrics should be investigated

Tools used: `pandas`, `numpy`, `matplotlib`, `seaborn`, `statsmodels`

---

## Data

The datasets used are the [Trending YouTube Video Statistics](https://www.kaggle.com/datasets/datasnaek/youtube-new) dataset from Kaggle, which contains daily records of trending YouTube videos for the US and GB.

- `USvideos.csv` — 40,949 rows of daily US trending video metrics
- `GBvideos.csv` — 38,916 rows of daily GB trending video metrics
- `US_category_id.json` — category ID to name mapping

> **Note:** The CSV files exceed GitHub's file size limits and are not hosted in this repository. To run the analysis locally, download the data from the Kaggle link above and place the files in the project root directory.

---

## How to Run

1. Clone the repository
2. Download the data files from Kaggle and place them in the project root
3. Install dependencies:
    ```bash
    pip install pandas numpy matplotlib seaborn statsmodels
    ```
4. Open `Trending_YouTube.ipynb` in Jupyter or run `Trending YouTube Video Statistics Simplified.py` directly in VS Code

---

## Key Findings

The data does not support the hypothesis that polarizing videos get shared the most.

- **Views correlate strongly with total interaction volume** — likes (0.87), dislikes (0.87), and comments (0.78) all scale with exposure, not polarization
- **The like-to-dislike ratio shows only a weak correlation with views (0.10)**, providing little evidence that polarization drives reach
- **Quantile analysis** I split videos into three equal tiers by polarization. The most polarizing tier had the *lowest* median views (~426K) vs. the middle tier (~646K)
- **Regression modeling** controlling for category and country confirmed that higher dislike rates are associated with slightly *lower* views (coefficient: -0.38 log units)
- **Category is the strongest predictor of reach** — Music videos had more than twice the median views of the next category (Comedy), while News & Politics ranked near the bottom despite being among the most polarizing content

**Conclusion:** Category and overall popularity are far stronger drivers of reach than polarization. The client's hypothesis is not supported by this data.

---

## Limitations & Future Work

- Views are used as a proxy for "getting shared the most" — a direct share count metric was not available in this dataset and would improve the analysis
- Future analysis could explore tags and video descriptions for keyword patterns associated with virality
- Sentiment analysis on titles or descriptions could provide a more nuanced measure of polarization than the like-to-dislike ratio
- Trending date patterns could reveal timing effects on view counts
