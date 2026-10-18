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

    plt.title('The Impact of Logistics Fulfillment Time on Return Rates', fontsize=14, pad=15)
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

    plt.title('Non-Linear Probability of Return vs. Logistics Fulfillment Time', fontsize=14, pad=15)
    plt.xlabel('Continuous Fulfillment Time (Hours)', fontsize=12)
    plt.ylabel('Predicted Probability of Return', fontsize=12)
    sns.despine()
    plt.tight_layout()
    plt.show()

def plot_impulse_penalty(df_intent):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    
    sns.barplot(
        data=df_intent, 
        x='User_Intent', 
        y='Return_Rate', 
        hue='User_Intent',
        palette=['#E67C73', '#5C6BC0', '#26A69A'], 
        legend=False,
        ax=ax1
    )

    ax1.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax1.set_ylim(0, df_intent['Return_Rate'].max() + 0.1)
    ax1.set_ylabel('Return Rate (The "Penalty")', fontsize=12, weight='bold')
    ax1.set_xlabel('User Session Intent', fontsize=12)
    
    for p in ax1.patches:
        if p.get_height() > 0:
            ax1.annotate(f'{p.get_height():.1%}', 
                         (p.get_x() + p.get_width() / 2., p.get_height()), 
                         ha='center', va='bottom', 
                         fontsize=11, weight='bold', xytext=(0, 5), textcoords='offset points')

    ax2 = ax1.twinx()
    sns.pointplot(
        data=df_intent, 
        x='User_Intent', 
        y='Avg_Session_Mins', 
        color='#424242', 
        markers='D', 
        linestyles='--',
        ax=ax2
    )

    ax2.set_ylabel('Avg. Decision Time (Minutes)', fontsize=12, color='#424242')
    ax2.set_ylim(0, df_intent['Avg_Session_Mins'].max() + 30) 

    for i, point in enumerate(df_intent['Avg_Session_Mins']):
        ax2.text(i, point + 5, f'{point:.1f} min', ha='center', va='bottom', fontsize=10, color='#424242')
    plt.title('The Myth of "Impulse Penalty": Return Rate vs. Decision Time', fontsize=14, pad=15)
    sns.despine(right=False)
    plt.tight_layout()
    plt.show()