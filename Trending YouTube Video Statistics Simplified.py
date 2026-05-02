# %% [markdown]
# In this project we will complete the following steps and answer the following questions:
# 1) Load your datasets and perform some simple exploratory data analysis.
# 2) Create a new column to represent the like-dislike ratio (likes divided by dislikes) for the videos in each dataset.
# 3) What is the average like-dislike ratio for all of the videos? (average number of likes per video divided by the average number of dislikes per video).
# 4) Perform data manipulation to find the average number of likes per video for the US and GB in the year 2018.
# 5) **Business report:** Your client hypothesizes that the most polarizing videos get shared the most. Analyze the data to determine whether your client is correct, and what other metrics should be investigated. Be sure to define any terms or cutoffs you make in the data. Present your findings in a short report for the client to review.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.formula.api as smf
import seaborn as sns

# Loading the table
df = pd.concat([
    pd.read_parquet('output/all_videos_final.parquet_0_0_0.snappy.parquet'),
    pd.read_parquet('output/all_videos_final.parquet_0_1_0.snappy.parquet'),
    pd.read_parquet('output/all_videos_final.parquet_0_2_0.snappy.parquet'),
    pd.read_parquet('output/all_videos_final.parquet_0_3_0.snappy.parquet')
])

print(df.shape)
print(df.dtypes)
display(df.head(10))

# %%
# Columns names were dropped in export.
# Renaming columns
df = df.rename(columns = {
    '_COL_0': 'video_id',
    '_COL_1': 'title',
    '_COL_2': 'channel_title',
    '_COL_3': 'category_title',
    '_COL_4': 'country', 
    '_COL_5': 'views',
    '_COL_6': 'likes',
    '_COL_7': 'dislikes',
    '_COL_8': 'comment_count',
    '_COL_9': 'publish_time',
    '_COL_10': 'days_trending'})

print(df.head())
print(df.dtypes)

# %%
# Views, likes, dislikes, comment count, and days trending should be integers
# Fix Snowflake Decimal type export issue
df[['views', 'likes', 'dislikes', 'comment_count', 'days_trending']] = (
    df[['views', 'likes', 'dislikes', 'comment_count', 'days_trending']].astype(float)
)

# publish_time should be datetime
df.publish_time = pd.to_datetime(df.publish_time)

print(df.dtypes)

# %%
# Creating df for each country
df_US_video = df[df['country'] == 'US']
df_GB_video = df[df['country'] == 'GB']

print("df_US duplicated sum:", df_US_video.duplicated().sum())
print("df_US unique video_id", df_US_video.video_id.nunique())
print("df_GB duplicated sum:", df_GB_video.duplicated().sum())
print("df_GB unique video_id:", df_GB_video.video_id.nunique())
print("df_US unique category_title:", df_US_video.category_title.nunique())
print("df_GB unique category_title:", df_GB_video.category_title.nunique())

# %%
# the dataframe has been aggregated previously in pipeline
# adding likes to dislike ratio column
# checking for zero dislikes as they will impact calculations
df_US_zero_dislikes = df_US_video[df_US_video['dislikes'] == 0]
print(df_US_zero_dislikes.count())
df_GB_zero_dislikes = df_GB_video[df_GB_video['dislikes'] == 0]
print(df_GB_zero_dislikes.count())

# %%
# 99 and 27 zero dislikes entries for both dataframes
# assigning NaN to zero dislikes removes 126 entries, which affects results very little
# they would be left skewing outliers that do not meaningfully add to our analysis at the moment
df_US_video['likes_to_dislikes'] = np.where(
    df_US_video['dislikes'] > 0,
    df_US_video['likes'] / df_US_video['dislikes'],
    np.nan
)
print(df_US_video.head())
print(df_US_video.isnull().sum())
df_GB_video['likes_to_dislikes'] = np.where(
    df_GB_video['dislikes'] > 0,
    df_GB_video['likes'] / df_GB_video['dislikes'],
    np.nan
)
print(df_GB_video.head())
print(df_GB_video.isnull().sum())

# %%
# now that the dataframes are aggregated, analyzing again
print(df_US_video.describe())
print(df_GB_video.describe())

# %% [markdown]
# The newly created likes to dislikes column is working as expected but the max is 840.75 and 1493.75. The method of tracking likes to dislikes as a ratio is unstable at extremely low dislike values making analysis harder. In the future, I would suggest using dislikes as a share of dislikes and likes together. This would bound the values between 0 and 1. But a ratio is what was in the instructions so I will continue.
# Many right skewed metrics exhist. For instance, US views average is 1.96M but the median is 518,107. This pattern happens across the board which indicates a small number of videos are driving a majority of the interactions.

# %%
# histogram function
def histogram(x, xlabel, title):
    log_x_us = np.log10(df_US_video[x] + 1) # log10 will continue to be used for our heavily skewed dataset
    log_x_gb = np.log10(df_GB_video[x] + 1) # +1 to avoid issues with 0
    plt.hist(log_x_us, bins=50, alpha=0.5, density=True, label='US') # overlaying both plots at 50% transparency
    plt.hist(log_x_gb, bins=50, alpha=0.5, density=True, label='GB') # both countries overlaying scaled to fit as GB is half of US dataset
    plt.legend()
    plt.xlabel(xlabel)
    plt.ylabel('Frequency')
    plt.title(title)
    plt.show()

histogram('views', 'Views (log scale)', 'Log Transformed Views Distribution')

# %%
# Great Britain has an even tighter spread than the US but still shares the same mode of 1 million. 
# This suggests while viral videos are similar in viewership in both countries, in Great Britain those viewerships are much more dramatic
# histogram of ratio
histogram('likes_to_dislikes', 'Ratio (log scale)', 'Log Transformed Likes to Dislikes Ratio Distribution')

# %%
# normal log dsitrobution in like to dislike ratio for both countries
# 10^1.5 is about 31.5 likes per dislike
# a steep drop off at 100 likes per dislike and 10 likes per dislike, very polarizing videos are actually rare
# histogram of likes
histogram('likes', 'Likes (log scale)', 'Log Transformed Likes Distribution')

print(df_US_video.count()) # validating the size of each dataset
print(df_GB_video.count())

# %%
# histogram spread is fairly symetrical and both countries look the same
# Because density is set True, we avoid the issue of the US dataset being larger
# histogram of dislikes
histogram('dislikes', 'Dislikes (log scale)', 'Log Transformed Dislikes Distribution')

# %%
# comment count histogram
histogram('comment_count', 'Comment Count (log scale)', 'Log Transformed Comment Count Distribution')

# %%
# histograms all look fairly symetrical in log scale and are similar between countries
# answering the question, "whats the average ratio for all videos?"
all_df_video = pd.concat([df_US_video, df_GB_video])

mean_ratio = (
    all_df_video['likes'].mean() /
    all_df_video['dislikes'].mean()
)
print(f'Average ratio of likes to dislikes: {mean_ratio:.2f}') # rounded 2 decimals
print(all_df_video.head())

# %%
# the average like-dislike ratio for all of the videos is 17.48 likes to dislikes
# finding the average number of likes per video for the US and GB in the year 2018
df_2018 = all_df_video[all_df_video['publish_time'].dt.year == 2018]
plt.hist(np.log10(df_2018.views + 1), bins=50, alpha=0.5, density=True, label='2018')
plt.hist(np.log10(all_df_video.views + 1), bins=50, alpha=0.5, density=True, label='All')
plt.xlabel('Likes (log scale)')
plt.ylabel('Frequency')
plt.title('Count of Views in Log Scale in 2018 and All')
plt.legend()
plt.show()
average_2018 = np.round(df_2018.views.mean(), 2)
print(f'Average views in 2018: {average_2018}')
median_2018 = np.round(df_2018.views.median(), 2)
print(f'Median views in 2018: {median_2018}')

# %%
# Average views in 2018 is approximately 3656840.82
# are the most polarizing videos getting shared the most?
# creating engagement rate column
all_df_video['engagement_rate'] = (
    (all_df_video['likes'] + all_df_video['dislikes'] + all_df_video['comment_count']) / # all likes, dislikes, and comments per view as "engegment rate"
    all_df_video['views']
)
plt.hist(np.log1p(all_df_video['engagement_rate']), bins=50) #log1p used to handle the right-skewed distribution; 
# note that views = 0 would cause division by zero in the engagement rate formula and should be filtered
plt.xlabel('Engagement Rate (log scale)')
plt.ylabel('Frequency')
plt.title('Engagement Rate Distribution in Log Scale')
plt.show()

# %% [markdown]
# During analysis I discovered an error in the engagement metric definition. After correcting the formula to (likes + dislikes + comments) / views, the distribution changed from symmetric to strongly right-skewed, which is more typical of engagement dynamics. Only a small number of videos capture a disproportionate level of interaction.

# %%
# creating a crosstable of variables
corr_matrix_all = all_df_video[[
    'views',
    'likes',
    'dislikes',
    'comment_count',
    'likes_to_dislikes',
    'engagement_rate']].apply(np.log1p).corr()
print(corr_matrix_all)

sns.heatmap(corr_matrix_all)
plt.show()

# %% [markdown]
# After correcting the engagement rate definition to (likes + dislikes + comments) / views, the relationship between views and engagement shifted from strongly positive to slightly negative. This makes more sense as views is now prominantly in the denominator, engagement measures density, and the largest audiences include higher proportions of passive viewers. 
# 
# What is correlative is views to likes (0.87), views to dislikes (0.87), and views to comments (0.78). These relationships suggest that interaction volume scales with exposure.
# 
# However, the like-to-dislike ratio shows weak correlation with views (0.10). This correlation is very weak to prove the theory that "polarizing" videos get the most shares."
# 
# One interesting relationship is likes_to_dislikes and engagement rate (0.47). The strongest correlation in our crosstable for these variables, showing some signs of increasing engagement, but not reach necessarily. 
# 
# What the data is demonstrating that views are strongly correlated with interaction counts (likes, dislikes, and comments), suggesting that interaction volume scales with exposure.
# 
# To further investigate the matter, I will split the data into quantiles of like to dislike ratio, analyzing how the highest quantile of ratio compares to the lowest.

# %%
# splitting ratio into quantiles
quantiles = all_df_video['likes_to_dislikes'].quantile(
    [0.1, 0.25, 0.5, 0.75, 0.9]
)
print(quantiles)

# %%
# applying quantiles to define a new column
all_df_video['Ratio Tier'] = pd.qcut(
    all_df_video['likes_to_dislikes'],
    q=3,
    labels=['High Polarization', 'Mid Polarization', 'Low Polarization'] # note: the smallest value is the highest polarization tier
)
print(all_df_video['Ratio Tier'].value_counts(normalize=True)) # validating the share of each tier

# %%
# each tier shares exactly a third of the data
# grouping by tier and median views in log scale
tiers_by_views = all_df_video.groupby('Ratio Tier', observed=True)['views'].apply( # observed True to ignore false values of which are none
    lambda x: np.log10(x)
    .median()
)
print(tiers_by_views)

order = ['High Polarization', 'Mid Polarization', 'Low Polarization']
box_mask = [
    np.log10(all_df_video.loc[all_df_video['Ratio Tier'] == tier, 'views'] + 1)
    for tier in order
    ] # mask for a boxplot of each category in same plot
plt.figure(figsize=(10,6))
plt.boxplot(box_mask, tick_labels=order)
plt.tight_layout()
plt.yticks(
    ticks=[2, 3, 4, 5, 6, 7, 8, 9],
    labels=['100', '1K', '10K', '100K', '1M', '10M', '100M', '1B'] # coverting the yticks back to readable numbers
)
plt.xlabel('Polarization Tier')
plt.ylabel('Views')
plt.title('View Distribution by Polarization Tier')

# %% [markdown]
# High Polarization: 10^5.63 ≈ 426k
# 
# Mid Polarization: 10^5.81 ≈ 646k
# 
# Low Polarization: 10^5.75 ≈ 562k
# 
# These are the figures for our 3 quantiles of likes to dislikes ratio. If the client’s hypothesis were correct, the most polarizing tier would exhibit the highest median views. But the highest group is the middle one, Mid Polarization, refuting the client's hypothesis further. Even the boxplots are close to identical.
# 
# The analysis shows a strong relationship between views and total engagement metrics including likes, dislikes, and comments, indicating that exposure is more correlative with engagement. However, the like-to-dislike ratio shows only a weak correlation with views (0.10), and highly polarizing videos do not exhibit higher median view counts. Therefore, the data provides little evidence that polarization is a primary driver of engagement. 
# 
# One final analysis, I will account for confounding variables like category and likes. Category has not been analyzed yet so next we take a look.

# %%
df_copy = all_df_video.copy() # analysis requires log scale, making copy of df to scale
df_copy['log_likes'] = np.log10(df_copy['likes'] + 1)
# creating new df grouped by category and ordered by median likes
order = df_copy.groupby('category_title', observed=False)['log_likes'].median().sort_values(ascending=False).index
box_mask = [df_copy.loc[df_copy['category_title'] == c, 'log_likes'] for c in order] # mask for a boxplot of each category in same plot
plt.figure(figsize=(10,6))
plt.boxplot(box_mask, tick_labels=order)
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.xlabel('Category')
plt.ylabel('Median Likes (log scale)')
plt.title('Median Likes by Category (log scale)')

# %%
# Music dominates in median likes while news and politics are the lowest
# Our polarization theory is not being supported still but more calculations to follow
# summary table of median values by categories
summary = (
    all_df_video
    .groupby('category_title', observed=True)
    .agg(
        median_views=('views', 'median'),
        median_likes=('likes', 'median'),
        median_ratio=('likes_to_dislikes', 'median')
    )
    .sort_values('median_views', ascending=False)
)
print(summary)        

# %% [markdown]
# Music is now more than twice the median views as the next category, Comedy. It also shows a high median ratio meaning much lower "polarization."
# Meanwhile, News & Politics is second to last with the lowest median ratio. If we accept our polarization theory, News & Politics should be higher on the list, further disproving our client. This table suggest category type is a strong driver of views and shares.
# 
# Next I will model regressions with categories and country as possible confounding variables. To improve the results, I will no longer use the dislike ratio as it is volatile in the highest values. Instead, I will calculate a dislike rate using the total likes and dislikes, binding our value range between 0 and 1.

# %%
# log trasnformed views (add 1 to avoid log(0))
df_copy['log_views'] = np.log10(df_copy['views'] + 1)
# log trasnformed likes
df_copy['log_likes'] = np.log10(df_copy['likes'] + 1)
# Create dislike rate (clean polarization metric)
df_copy['dislike_rate'] = df_copy['dislikes'] / (df_copy['likes'] + df_copy['dislikes'] + 1)
model = smf.ols(
    'log_views ~ dislike_rate + C(category_title) + C(country)',
    data=df_copy
).fit()
print(model.summary())

# %%
# A 1-unit increase in dislike_rate is associated with a 0.38 unit decrease in log_views.
# This suggests negatively received videos are not generating greater reach or views.
# Trying log_likes as a controlled variable
model = smf.ols(
    'log_views ~ dislike_rate + C(category_title) + log_likes',
    data=df_copy
).fit()
print(model.summary())

# %%
# checking engagement rate against dislike rate
df_copy['log_engagement'] = np.log10(df_copy['engagement_rate'] + 1)
model = smf.ols(
    'log_engagement ~ dislike_rate + C(category_title) + C(country)',
    data=df_copy
).fit()
print(model.summary())

# %% [markdown]
# When controlling for category and country, dislike rate shows a slight negative association with views. When controlling additionally for total likes, that relationship reversed, and R^2 increases to 0.79, suggesting that among similarly popular videos, disagreement does correspond with a slightly higher reach. However, given the direct causal relationship between views and likes, the results should be interpreted cautiously, and likely is a proxy for "how popular is a video among already-seen videos."
# 
# After correcting the engagement rate function, R^2 dropped from 0.16 to 0.11, meaning before the metric was inflated by capturing volume rather than density, which is what the column should measure. However, the findings are similar: higher dislike rates are associated with lower engagement having a coefficient of -0.0146. That means more polarization slightly decreases overall engagement which is a direct refutation of the client's theory. 
# 
# In conclusion, this analysis examining a few questions including whether highly polarized YouTube videos received greater engagement and reach. After exploratory analysis, quantile comparisons, and regression modeling, the data does not provide strong evidence that polarization drives views.
# 
# Key findings include:
# - Views are strongly associated with overall engagement metrics including likes and comments.
# - The like-to-dislike ratio shows only a weak relationship with views.
# - When controlling for category and country, higher dislikes are associated with slightly lower views.
# - Additionally when controlling for likes, the relationship reversed. This effect should be interpreted cautiously due to the direct relationship between views and likes, but the implication is that among similarly viewed videos, disagreement does correspond with higher reach.
# - Categories explain the most substantial variation in views rather than polarization.
# 
# Overall, the evidence suggests that category and likes are stronger predictors of reach than disagreement. While some data implies polarization can generate some views between similarly levels of shared videos, it does not appear to systematically drive higher view counts in this dataset.
# 
# It's important to note we are using views as a measurement of "getting shared the most," which is not the most direct. A direct measurement was not provided and future analysis should incorporate true sharing metrics for better analysis.
# 
# Category ID, trending date, tags, and even a breakdown of the description columns could also be investigated further. Categories and tags help tell what content is most popular. We could find key words that help uncover viral terms or phrases that help attract view shares or create a sentiment analysis. And while we used publish date as the default datetime measuremnt, trending times can be analyzed for patterns as well, though it would require more dimensional calculations.

# %% [markdown]
# 


