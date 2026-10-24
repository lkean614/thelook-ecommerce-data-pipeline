import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

def plot_logistics_trend(df_logistics):    
    bins = [0, 24, 48, 72, 96, 120, np.inf]
    labels = ['<24h', '24-48h', '48-72h', '72-96h', '96-120h', '>120h']
    
    df = df_logistics.copy()
    df['fulfillment_bin'] = pd.cut(df['total_fulfillment_time_hours'], bins=bins, labels=labels)
    return_rates = df.groupby('fulfillment_bin', observed=False)['return_flag'].mean().reset_index()

    plt.figure(figsize=(10, 6))
    primary_color = '#B22222'
    ax = sns.pointplot(
        data=return_rates, 
        x='fulfillment_bin', 
        y='return_flag', 
        color=primary_color, 
        markers='o', 
        linestyles='-'
    )

    y_min = return_rates['return_flag'].min() - 0.02
    y_max = return_rates['return_flag'].max() + 0.02
    y_min = max(0, y_min) 
    ax.set_ylim(y_min, y_max)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    x_indices = np.arange(len(return_rates))
    plt.fill_between(
        x_indices, 
        return_rates['return_flag'], 
        y_min,
        color=primary_color, 
        alpha=0.08
    )

    for i, point in enumerate(return_rates['return_flag']):
        ax.text(i, point + 0.002, f'{point:.1%}', ha='center', va='bottom', fontsize=10)

    plt.title('Return Rate by Fulfilment Time', fontsize=14, pad=15)
    plt.xlabel('Fulfillment Time (Hours)', fontsize=12)
    plt.ylabel('Return Rate', fontsize=12, weight='bold')
    sns.despine()
    plt.tight_layout()
    plt.show()

def plot_logistic_return_probability(df_logistics):
    plt.figure(figsize=(10, 6))

    ax = sns.regplot(
        data=df_logistics, 
        x='total_fulfillment_time_hours', 
        y='return_flag', 
        logistic=True,
        n_boot=500,
        scatter_kws={'alpha': 0.05, 'color': '#708090', 's': 15},
        line_kws={'color': '#B22222', 'linewidth': 3}
    )

    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.0%}'.format(y)))
    ax.set_ylim(0, 1.05)

    plt.title('Fitted Probability of Return vs. Fulfilment Time (logistic regression)', fontsize=14, pad=15)
    plt.xlabel('Continuous Fulfillment Time (Hours)', fontsize=12)
    plt.ylabel('Predicted Probability of Return', fontsize=12)
    sns.despine()
    plt.tight_layout()
    plt.show()


def _wilson_ci(k, n, z=1.96):
    """Wilson score interval for a proportion k/n."""
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def plot_impulse_penalty(df_intent, rate_col='return_rate_delivered'):
    """Return rate by session intent, with 95% Wilson CIs.

    rate_col: 'return_rate_delivered' (returned / delivered items, default)
              or 'return_rate_all_items' (returned / all matched items).
    """
    order = ['Impulse Buyers', 'Targeted Searchers', 'Heavy Browsers']
    df = df_intent.set_index('User_Intent').loc[order].reset_index()

    if rate_col == 'return_rate_delivered':
        n_col, base = 'delivered_items', 'delivered items'
    else:
        n_col, base = 'items', 'all items'

    k = df['returned_items'].astype(float)
    n = df[n_col].astype(float)
    rates = k / n
    ci = np.array([_wilson_ci(a, b) for a, b in zip(k, n)])
    err = np.vstack([rates - ci[:, 0], ci[:, 1] - rates])

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df['User_Intent'], rates, yerr=err, capsize=6,
           color=['#E67C73', '#5C6BC0', '#26A69A'])

    for x, (r, hi) in enumerate(zip(rates, ci[:, 1])):
        ax.annotate(f'{r:.1%}', (x, hi), textcoords='offset points',
                    xytext=(0, 5), ha='center', fontsize=11, weight='bold')

    ax.set_xticks(range(len(df)))
    ax.set_xticklabels([
        f"{name}\n(avg session {mins:.0f} min, n={int(cnt):,})"
        for name, mins, cnt in zip(df['User_Intent'], df['avg_session_mins'], n)
    ])
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.set_ylim(0, ci[:, 1].max() * 1.25)
    ax.set_ylabel(f'Return rate ({base})', fontsize=12)
    ax.set_title('Return Rate by Session Intent (95% CI)', fontsize=14, pad=15)
    sns.despine()
    plt.tight_layout()
    plt.show()

def plot_match_gap_hist(gaps, window_hours=24, chosen=(-1, 4)):
    """Histogram of (order created - purchase event) in hours for matched order items.
    gaps: DataFrame with gap_hour (floor of the signed gap in hours) and items.
    chosen: (start_h, end_h) of the window used by the mart, shaded for reference (None to skip)."""
    fig, ax = plt.subplots(figsize=(10, 4))
    if chosen is not None:
        ax.axvspan(chosen[0], chosen[1], color='#26A69A', alpha=0.15,
                   label=f'Window used in the mart ({chosen[0]}h to +{chosen[1]}h)')
    ax.bar(gaps['gap_hour'], gaps['items'], width=0.9, align='edge', color='#5C6BC0')
    ax.axvline(0, color='k', lw=0.8)
    ax.set_xlabel('Order created minus purchase event (hours; negative = order created first)')
    ax.set_ylabel('Matched order items')
    ax.set_title(f'Time gap between purchase event and order (nearest session, within ±{window_hours}h)')
    if chosen is not None:
        ax.legend(frameon=False)
    sns.despine()
    plt.tight_layout()
    plt.show()