# Signal Mosaic:
# Systematic Multi-Asset Funds with Coverage-Aware News Sentiment

**FINS3645 Financial Market Data Design & Analysis — Project B**

## DRAFT FOR STUDENT REVIEW

This Phase 1 draft organises verified project evidence and proposes interpretations. All paragraphs marked [STUDENT REVIEW REQUIRED] must be reviewed, rewritten where necessary, and approved by the student before the report is converted into its final Word and PDF submission formats.

This notice is for the Markdown draft only. Do not assume it will appear in the final submitted report.

## Executive Summary

Signal Mosaic is a Project B investment-product prototype that combines structured market data and unstructured equity headlines. The product contains eleven walk-forward out-of-sample funds across equity-only, crypto-only, combined equity-plus-crypto, and equity sentiment-overlay strategies. The structured data are 50 US equities across ten sectors and 10 cryptocurrencies. The unstructured data are equity headlines, scored with plain VADER and converted into a daily sector sentiment index.

The fund engine uses a 2020 initial estimation period, expanding-window estimation, monthly rebalancing, and weights formed from information available before each holding period. Equity and combined funds begin live evaluation on 2021-01-04 and end on 2023-12-29. Crypto-only funds begin on 2021-01-01 and end on 2023-12-31 because they use the native seven-day crypto calendar. Sharpe ratios use a risk-free rate of zero, and net returns include a 10 basis-point one-way turnover-cost assumption after initial establishment.

[STUDENT REVIEW REQUIRED — Economic interpretation] The strongest headline fund result was Crypto Minimum Variance, which recorded the highest net annualised return at 49.25% and the highest net Sharpe ratio at 0.91. That result must be read together with its 76.12% annualised volatility and -73.55% maximum drawdown. Within the combined equity-plus-crypto family, Combined Risk Parity had the highest net Sharpe ratio at 0.78, while Combined Minimum Variance had the lowest annualised volatility across all funds at 12.72%.

The standalone sentiment index scored 146,830 valid equity headlines and produced 10,060 date-sector rows. Plain VADER classified 49.57% of scored headlines as neutral and 48.85% as exact-zero compound scores. Missing-news sector-days remained missing rather than being converted into neutral sentiment, and all investable sentiment fields were lagged by at least one complete trading day.

[STUDENT REVIEW REQUIRED — Economic interpretation] The sentiment-fusion test did not show that plain VADER sentiment improved the equity fund. Equity Equal Weight recorded a 12.61% net annualised return and 0.82 net Sharpe. Equity Naive Sentiment Tilt recorded 11.65% and 0.77, while Equity Coverage-Gated Sentiment Tilt recorded 11.91% and 0.78. The Coverage-Gated design reduced some of the Naive Tilt shortfall, but the pooled sentiment-return Spearman correlation remained negative at -0.0705.

[STUDENT REVIEW REQUIRED — Product positioning] The Coverage Lens is the main Signal Mosaic product extension. It does not prove that a signal is true or predictive. It shows whether sector sentiment rests on broad or concentrated news coverage, which can support more transparent disclosure and more cautious signal use.

## 1. Funds and Walk-Forward Backtest Design

Signal Mosaic builds funds from three return universes. The equity universe contains 50 US equities across ten sectors. The crypto universe contains 10 cryptocurrencies. The combined universe contains the 50 equities plus the 10 cryptocurrencies, but it is evaluated on the equity trading calendar. Crypto-only returns are computed on the native seven-day calendar and annualised with 365 observations per year. Equity and combined returns are annualised with 252 observations per year.

The initial estimation period is 2020. For equity and combined funds, usable estimation returns run from 2020-01-03 to 2020-12-31, and the first live return is 2021-01-04. For crypto-only funds, estimation returns run from 2020-01-02 to 2020-12-31, and the first live return is 2021-01-01. These first-live dates are recorded in the backtest design table and performance metrics table.

[INSERT TABLE 1 HERE:
Source file: results/tables/fund_backtest_design.csv
Purpose: Document sample dates, calendars, annualisation, window type, rebalance rule, training rule, constraints, risk-free-rate assumption, and transaction-cost assumption.
Required columns: fund_name, asset_family, method, calendar, annualisation_factor, initial_estimation_start, initial_estimation_end, first_live_date, end_date, window_type, rebalance_rule, training_rule, holding_rule, max_target_weight, risk_free_rate, transaction_cost_rate.
Proposed caption: Table 1. Walk-forward backtest design and assumptions by fund family and method.
Student interpretation required: No]

At each monthly rebalance date, the optimiser uses returns strictly before the rebalance date. The rebalance date is the first available observation of each calendar month. Target weights become effective for that date's return because they were formed with information through the previous observation. Between rebalances, portfolio weights drift with realised daily asset returns. The next rebalance trades from the drifted pre-trade weights to the new target weights.

The base method set has three rules. Equal Weight allocates 1/N across the assets in the relevant universe. Minimum Variance solves for long-only, fully invested weights that minimise the estimated covariance-based variance, without expected-return estimates. Risk Parity solves for long-only, fully invested weights that bring asset risk contributions close to equal. The optimised funds use a 20% maximum target weight per asset. Equal Weight is not changed by that cap.

Transaction costs are included as a robustness assumption. The model charges 10 basis points per dollar of one-way turnover at scheduled rebalances after inception. Turnover is defined as one half of the sum of absolute differences between target weights and drifted pre-trade weights. The initial portfolio establishment cost is excluded. Gross and net return histories are both retained, but the report uses net results for headline comparisons.

The combined funds use same-date native crypto returns left-joined to the equity return calendar. Weekend-only crypto returns are intentionally excluded from the combined fund panel because that combined product is evaluated on equity trading days. Crypto-only funds retain weekend returns and are evaluated on the native seven-day calendar.

[STUDENT REVIEW REQUIRED — Economic interpretation] This design is intended to make the comparison investable in the backtest sense: each reported fund return is generated after an initial estimation period and after weights have been formed from past data only. The design still remains a historical simulation, not live performance, and it does not prove that the same fund rankings would persist outside 2021-2023.

## 2. Out-of-Sample Results and Fund Fact Sheets

The final performance metrics table contains eleven funds. The base set includes Equity Equal Weight, Equity Minimum Variance, Equity Risk Parity, Crypto Equal Weight, Crypto Minimum Variance, Crypto Risk Parity, Combined Equal Weight, Combined Minimum Variance, and Combined Risk Parity. The fusion stage adds Equity Naive Sentiment Tilt and Equity Coverage-Gated Sentiment Tilt. All funds have net return, net volatility, net Sharpe, maximum drawdown, turnover, transaction-cost, holding-count, and largest-current-weight fields.

[INSERT TABLE 2 HERE:
Source file: results/tables/performance_metrics.csv
Purpose: Compare net performance and implementation metrics across all eleven funds.
Required columns: fund_name, asset_family, method, first_live_date, end_date, number_of_observations, annualisation_factor, cumulative_return_net, annualised_return_net, annualised_volatility_net, Sharpe_net, maximum_drawdown_net, average_rebalance_turnover, total_transaction_cost, current_number_of_holdings, largest_current_weight.
Proposed caption: Table 2. Net out-of-sample performance metrics across the eleven Signal Mosaic funds.
Student interpretation required: Yes]

[INSERT FIGURE 1 HERE:
Source file: results/figures/fund_risk_return_comparison.png
Purpose: Show net annualised return against net annualised volatility across funds.
Proposed caption: Figure 1. Net risk-return comparison across Signal Mosaic funds, 2021-2023.
Student interpretation required: Yes]

Crypto Minimum Variance has the highest net annualised return, 49.25%, and the highest net Sharpe ratio, 0.91. Crypto Risk Parity follows with a 41.69% net annualised return and 0.84 net Sharpe, while Crypto Equal Weight records 40.41% and 0.83. The crypto results use 1,095 daily observations and a 365-day annualisation factor. Their maximum drawdowns are severe: -73.55% for Crypto Minimum Variance, -80.49% for Crypto Risk Parity, and -81.59% for Crypto Equal Weight.

[STUDENT REVIEW REQUIRED — Economic interpretation] The crypto funds dominate the return ranking in this sample, but they do not dominate on capital preservation. Their drawdowns are far larger than those of the equity and combined funds. The student should decide how strongly to frame this trade-off, because the metric table alone does not prove that higher crypto returns compensated all investors for the realised risk.

Among the equity-only base methods, Equity Equal Weight has a 12.61% net annualised return, 16.12% annualised volatility, 0.82 net Sharpe, and -20.26% maximum drawdown. Equity Risk Parity has lower return at 10.04%, lower volatility at 14.93%, 0.72 net Sharpe, and -19.41% maximum drawdown. Equity Minimum Variance has the lowest equity volatility at 12.73% and the least negative maximum drawdown at -17.84%, but its net annualised return is 7.05% and its net Sharpe is 0.60.

[STUDENT REVIEW REQUIRED — Economic interpretation] The equity results suggest a familiar risk-control trade-off: Minimum Variance reduced volatility and drawdown but also gave up return, while Equal Weight retained broader equity exposure and had the strongest equity Sharpe in this sample. The student should review this wording because it describes a pattern rather than a proven causal mechanism.

The combined funds show a different ranking. Combined Equal Weight has the highest combined-family return at 15.08%, with 21.60% volatility, 0.76 net Sharpe, and -27.90% maximum drawdown. Combined Minimum Variance has 7.05% return, 12.72% volatility, 0.60 Sharpe, and -17.84% drawdown. Combined Risk Parity has 12.75% return, 17.44% volatility, 0.78 Sharpe, and -22.40% drawdown, making it the strongest combined fund by net Sharpe.

[INSERT FIGURE 2 HERE:
Source file: results/figures/fund_growth_of_one_by_family.png
Purpose: Compare net growth of one dollar within equity, crypto, and combined fund families.
Proposed caption: Figure 2. Net growth of one dollar by family and method.
Student interpretation required: Yes]

[INSERT FIGURE 3 HERE:
Source file: results/figures/fund_drawdowns_combined.png
Purpose: Compare combined-fund net drawdowns across methods.
Proposed caption: Figure 3. Combined-fund net drawdowns across Equal Weight, Minimum Variance, and Risk Parity.
Student interpretation required: Yes]

The latest holdings table provides the current target holdings for every fund. Equity Equal Weight holds 50 equities at 2.00% each. Crypto Equal Weight holds 10 cryptocurrencies at 10.00% each. The optimised funds concentrate more. Equity Minimum Variance reports 12 current non-zero holdings and a largest current weight of 19.82%. Crypto Minimum Variance reports 8 current non-zero holdings and a largest weight of 20.00%. Combined Minimum Variance reports 12 current non-zero holdings, a largest weight of 19.84%, and the latest target allocation sums to 100.00% equity and 0.00% crypto by asset class.

[STUDENT REVIEW REQUIRED — Economic interpretation] The latest Combined Minimum Variance allocation indicates that, at the final rebalance, the optimiser did not materially allocate to crypto. This statement should be kept narrow: it describes the latest target holdings, not every rebalance and not an investment recommendation to avoid crypto.

Transaction-cost effects are recorded but small in rate terms relative to the scale of realised volatility and drawdown. Total recorded transaction-cost rates range from 0.000902 for Equity Risk Parity to 0.002431 for Crypto Minimum Variance. Average rebalance turnover ranges from 2.51% for Equity Risk Parity to 6.75% for Crypto Minimum Variance. The sentiment tilts increase turnover relative to Equity Equal Weight: 4.74% for Coverage-Gated and 5.47% for Naive versus 2.65% for Equity Equal Weight.

Each fact sheet is designed to show growth of one dollar, drawdown, annualised return, annualised volatility, Sharpe ratio, current holdings, rebalance assumptions, and transaction-cost assumptions. Representative fact sheets should include Equity Equal Weight as the transparent equity base, Crypto Minimum Variance as the highest-return and highest-Sharpe fund, Combined Risk Parity as the strongest combined fund by Sharpe, and Equity Coverage-Gated Sentiment Tilt as the Signal Mosaic innovation fund.

[STUDENT REVIEW REQUIRED — Product positioning] These fact sheets can help an investor compare fund behaviour without reading the modelling code. The student should review this claim because "help" is an investor-usefulness judgment, and the app is not providing personal financial advice.

## 3. Standalone Sector Sentiment Index

The sentiment stage applies plain NLTK VADER to preserved equity headline text. The implementation scores each headline individually and retains original casing, punctuation, negation, intensifiers, and word order. It does not lowercase titles, strip punctuation, remove stopwords, or concatenate titles before scoring. Missing titles are not scored. Crypto is not scored because the project contains no crypto headline data.

The cleaned headline set contains 146,836 rows. Of these, 146,830 headlines are scored and 6 are unscored because of missing titles. The scoring diagnostics report 54,980 positive headlines, 72,786 VADER-neutral headlines, and 19,064 negative headlines using the standard compound-score thresholds. This corresponds to 37.44% positive, 49.57% neutral, and 12.98% negative. The exact-zero compound count is 71,720, or 48.85% of scored headlines.

[STUDENT REVIEW REQUIRED — Critical reflection] The neutral share should not be read as proof that half of the news was economically neutral. The local data guide warns that headline sentiment is a noisy proxy and that many finance headlines can be neutral under plain VADER. The student should decide whether to emphasise this as a limitation of plain VADER, a motivation for later human-labelled validation, or both.

Headline scores are aggregated in two steps. First, headline-level scores are averaged to ticker-day sentiment for each trading date and ticker with at least one headline. This creates 37,962 ticker-days. Second, sector sentiment is built by equal-weighting available ticker-day mean compound scores within each sector. A ticker with 20 headlines counts as one ticker-day observation at the sector stage, not as 20 times the weight of a ticker with one headline.

The sector sentiment artifact uses a complete equity-date-sector grid with 10,060 rows: 1,006 equity trading dates times ten sectors. There are 9,832 sector-days with news and 228 sector-days without news. Missing-news sector-days have raw sentiment left blank rather than filled with zero. A genuine calculated zero remains distinguishable from a missing value. The artifact also includes one-trading-day lagged raw sentiment, 21-trading-day trailing sentiment, and lagged 21-trading-day trailing sentiment.

[INSERT FIGURE 4 HERE:
Source file: results/figures/sector_sentiment_timeseries.png
Purpose: Show 21-trading-day trailing sector sentiment across the ten equity sectors.
Proposed caption: Figure 4. Plain-VADER sector sentiment over time, headline-aligned dates.
Student interpretation required: Yes]

The timing rule is explicit. A raw sector score belongs to the trading day to which headlines are aligned, but it cannot affect a position held on that same day. If a Saturday headline maps to Monday, and a Monday headline also maps to Monday, both contribute to Monday's raw sector index. Neither can affect Monday's position; they first become available for Tuesday.

Coverage fields reconcile with the foundation coverage panel. For each sector-date, the sentiment artifact includes article count, covered tickers, coverage share, breadth, and a news flag. These fields allow sentiment to be displayed with the amount and breadth of supporting headline coverage rather than as a stand-alone number.

## 4. Innovation: Coverage-Gated Sentiment Fusion

The Signal Mosaic innovation is a coverage-aware sentiment overlay for equity sectors. The comparison base is Equity Equal Weight because it gives each of the ten equity sectors a 10% strategic weight and each stock within a sector an equal share. This base isolates the effect of the sentiment overlay from optimiser-specific sector allocations.

Coverage share is defined as covered sector tickers divided by five. Breadth is defined as one divided by five times the sum of squared ticker headline shares within a sector. Breadth near one indicates that headlines are distributed more evenly across the five stocks in the sector. Breadth near 0.2 indicates that one ticker dominates the sector's news coverage.

[STUDENT REVIEW REQUIRED — Product positioning] The Coverage Lens is useful as a disclosure layer because it separates a sentiment reading from the evidence structure beneath it. The student should review this statement because it describes potential investor usefulness, not a measured improvement in investment performance.

[INSERT FIGURE 6 HERE:
Source file: results/figures/sentiment_coverage_context.png
Purpose: Display sector sentiment together with coverage context.
Proposed caption: Figure 6. Sector sentiment with Coverage Lens context.
Student interpretation required: Yes]

At each monthly equity rebalance, the fusion stage uses only the look-ahead-safe field `vader_compound_21d_trailing_lag1`. Sector sentiment is standardised cross-sectionally across available sectors on that rebalance date, clipped to the interval from -2 to +2, and then multiplied by a fixed alpha of 0.15. If fewer than two sector signals are available, or if cross-sectional variance is zero, the policy applies no active tilt. Missing sector signals are not converted into sentiment zero; they receive no active view.

The Naive Sentiment Tilt uses a sector multiplier equal to one plus 0.15 times the sector z-score. The Coverage-Gated Sentiment Tilt uses one plus 0.15 times coverage quality times the sector z-score. Coverage quality equals lagged 21-day coverage share multiplied by lagged 21-day breadth. The coverage variables are shifted one full equity trading day before use. Coverage quality is therefore an attenuation term, not a sentiment score.

The fusion signal diagnostics contain 360 rebalance-sector observations: 36 monthly rebalances times ten sectors. All 360 have valid sentiment observations. Mean coverage quality is 0.7953, with a minimum of 0.4396 and maximum of 0.9934. The coverage gate reduces the absolute active tilt in 93.61% of rebalance-sector observations. Maximum sector weights are 13.14% for the Naive Tilt and 12.75% for the Coverage-Gated Tilt; minimum sector weights are 6.99% and 7.35%, respectively.

[INSERT TABLE 3 HERE:
Source file: results/tables/fusion_before_after.csv
Purpose: Compare Equity Equal Weight, Equity Naive Sentiment Tilt, and Equity Coverage-Gated Sentiment Tilt.
Required columns: fund_name, annualised_return_net, annualised_volatility_net, Sharpe_net, maximum_drawdown_net, cumulative_return_net, average_rebalance_turnover, total_transaction_cost, number_of_rebalances, change_in_return_vs_base, change_in_volatility_vs_base, change_in_Sharpe_vs_base, change_in_max_drawdown_vs_base.
Proposed caption: Table 3. Before-versus-after sentiment fusion results.
Student interpretation required: Yes]

The before-versus-after table reports that Equity Equal Weight has a 12.61% net annualised return, 16.12% net volatility, 0.82 net Sharpe, -20.26% maximum drawdown, and 42.59% cumulative net return. Equity Naive Sentiment Tilt has an 11.65% net annualised return, 15.97% volatility, 0.77 net Sharpe, -20.13% maximum drawdown, and 39.00% cumulative net return. Equity Coverage-Gated Sentiment Tilt has an 11.91% net annualised return, 16.00% volatility, 0.78 net Sharpe, -20.14% maximum drawdown, and 39.98% cumulative net return.

[INSERT FIGURE 5 HERE:
Source file: results/figures/fusion_growth_of_one.png
Purpose: Show net growth of one dollar for Equity Equal Weight, Naive Sentiment Tilt, and Coverage-Gated Sentiment Tilt.
Proposed caption: Figure 5. Equity Equal Weight versus sentiment-overlay growth of one dollar.
Student interpretation required: Yes]

[STUDENT REVIEW REQUIRED — Economic interpretation] The measured fusion result is negative relative to Equity Equal Weight. Both sentiment tilts reduce net annualised return and net Sharpe. The Coverage-Gated Tilt performs better than the Naive Tilt by losing less return and Sharpe, but it still does not beat the base fund. This should be presented as an evaluated extension with a cautious result, not as a successful alpha signal and not as a simple failure.

The predictive diagnostics compare monthly sector sentiment z-scores with next-rebalance-period sector returns. The pooled Spearman correlation is -0.0705 for all valid observations. Above median coverage quality, the pooled Spearman correlation is -0.0398. At or below median coverage quality, it is -0.0992. Average cross-sectional monthly Spearman correlations are also negative in all three samples. The median coverage split is descriptive and was not used to retune alpha or choose a threshold.

[STUDENT REVIEW REQUIRED — Economic interpretation] These rank correlations do not support a positive predictive relationship in the observed sample. They also do not prove that sentiment can never work. The correct inference is narrower: this particular plain-VADER, fixed-alpha, coverage-gated design did not show positive predictive value over this 2021-2023 evaluation.

## 5. Signal Mosaic App and Investor Journey

The Streamlit app is a presentation and interaction layer over precomputed artifacts. It has six sections: Overview, Compare Funds, Fund Fact Sheet, Allocation Studio, Sentiment & Coverage, and Methodology & Limitations. The app reads committed CSV artifacts from the results folder, validates their schemas, caches CSV loading, and uses paths relative to the project root.

The Overview page summarises the fund count, sector count, out-of-sample window, pipeline validation count, fund shelf, and evidence highlights. Compare Funds lets a user filter by asset family and method, select two to six funds, compare net performance metrics, view growth of one dollar, risk-return position, Sharpe, and drawdown, and download the selected comparison table. The Fund Fact Sheet page shows a selected fund's performance cards, growth path, drawdown path, current holdings, method summary, and downloadable return and holdings tables.

The Allocation Studio is explicitly an illustrative fund-of-funds view, not a twelfth managed fund. It lets the user select between two and five precomputed funds and enter weights. The app normalises non-zero weights to 100%, compounds each selected fund's daily net returns within each calendar month, aligns the selected funds on their shared monthly sample, and calculates a monthly rebalanced allocation. Metrics use 12 periods per year and no additional allocation-level transaction cost.

[STUDENT REVIEW REQUIRED — Product positioning] This monthly allocation design gives users a practical way to compare mixed-calendar funds without inserting artificial daily returns. The student should review this statement because it is a product-positioning claim about user value, even though the underlying monthly compounding method is directly implemented.

The Sentiment & Coverage page lets users choose sectors, date ranges, and sentiment views. It shows VADER compound sentiment with a zero reference, then displays coverage context separately through article count, covered tickers, coverage share, and breadth. It also displays the plain-VADER neutral share and the before-versus-after fusion result. The Methodology & Limitations page explains the Data Factory Floor, fund design, sentiment design, Coverage-Gated innovation, and pipeline status.

The deployment architecture is intentionally light. The app does not load raw market data, load raw headlines, call the data-access helper, run build scripts, execute the orchestration pipeline, import NLTK, initialise VADER, optimise portfolios, rebuild sentiment, rebuild fusion, write analytical files, or depend on Project A. The pipeline validation table reports 81 PASS rows and the app artifact inventory reports nine ready app-facing artifacts.

[STUDENT REVIEW REQUIRED — Product positioning] The app design supports transparency by keeping fund performance, holdings, sentiment, coverage, methodology, and limitations visible in the same product journey. The student should review this framing because it moves beyond implementation facts into a judgement about investor communication.

## 6. Critical Reflection and Three Recommendations

[STUDENT REVIEW REQUIRED — Critical reflection] The strongest limitation is the short 2021-2023 out-of-sample period. It contains only 753 equity-calendar fund observations for equity and combined funds and 1,095 observations for crypto-only funds. The project therefore measures a specific historical period rather than a stable long-run distribution of fund behaviour.

[STUDENT REVIEW REQUIRED — Critical reflection] The asset universe is narrow. The equity set contains 50 large US equities and the crypto set contains 10 cryptocurrencies. The results may be sensitive to the selected securities, sector composition, and crypto names. There is no external validation dataset in the local project.

[STUDENT REVIEW REQUIRED — Critical reflection] The sentiment model uses headlines only, not full article text. Plain VADER is transparent and reproducible, but it leaves 49.57% of scored headlines neutral and 48.85% as exact-zero compound scores. That creates a false-neutral risk for finance headlines whose economic content may not be captured by general-purpose lexicon rules.

[STUDENT REVIEW REQUIRED — Critical reflection] The project has no crypto sentiment data, so the sentiment and Coverage Lens features apply only to equities. The combined funds include crypto returns, but the fusion stage does not tilt crypto or combined funds directly. This limits what the sentiment result can say about the multi-asset product as a whole.

[STUDENT REVIEW REQUIRED — Critical reflection] The transaction-cost model is deliberately simple. It applies 10 basis points per dollar of one-way turnover, excludes initial establishment cost, and does not model taxes, market impact, custody, management fees, borrow costs, liquidity constraints, or trade-size effects. These omissions matter if the prototype is interpreted as a real investment product.

[STUDENT REVIEW REQUIRED — Critical reflection] The combined funds exclude weekend-only crypto returns because the combined panel is evaluated on the equity calendar. This is internally consistent with the design, but it means combined-fund performance is not the same as a continuously traded crypto allocation. The Allocation Studio also moves to a common monthly calendar when combining precomputed funds.

[STUDENT REVIEW REQUIRED — Critical reflection] The Coverage Lens measures the structure of headline evidence, not the truth of the news and not predictive power. The fusion diagnostics are negative in this sample, so coverage should be presented as a risk-control and disclosure mechanism unless future validation shows positive predictive value.

[STUDENT REVIEW REQUIRED — Recommendation] Recommendation 1 — Extend evaluation before commercial use. The next stage should test a longer out-of-sample period, multiple market regimes, rolling or multiple-origin validation, stress periods, frozen parameter decisions, transaction-cost sensitivity, and separate validation of the crypto calendar assumptions. This recommendation follows from the short 2021-2023 window and the severe crypto drawdowns.

[STUDENT REVIEW REQUIRED — Recommendation] Recommendation 2 — Improve sentiment only through validated model comparison. Plain VADER should remain the transparent baseline. Any finance lexicon or finance-specific model should be evaluated against a manually labelled representative headline sample and a separate holdout period. The comparison should test neutral, positive, and negative classification quality, and a new model should not be selected solely because it improves the backtest.

[STUDENT REVIEW REQUIRED — Recommendation] Recommendation 3 — Use Coverage Lens primarily as signal-risk control and disclosure. The app should continue to display coverage beside sentiment, preserve missing-news warnings, and attenuate active tilts when coverage is narrow. Equal Weight should remain the transparent default until a sentiment overlay produces positive out-of-sample evidence. Coverage should not be marketed as predictive proof.

## 7. Conclusion

Signal Mosaic successfully builds the Part B analytical product: eleven out-of-sample funds, validated fund fact sheets, a standalone equity-sector sentiment index, a look-ahead-safe sentiment fusion extension, and a Streamlit app that loads precomputed artifacts. The pipeline validation table reports 81 PASS rows, and the app artifact inventory reports nine ready app-facing artifacts.

[STUDENT REVIEW REQUIRED — Economic interpretation] The fund evidence is mixed rather than promotional. Crypto Minimum Variance leads return and Sharpe rankings but has large drawdown. Combined Risk Parity is the strongest combined fund by Sharpe. Equity Equal Weight remains stronger than both sentiment overlays in the equity fusion comparison.

[STUDENT REVIEW REQUIRED — Economic interpretation] The sentiment evidence does not show positive predictive value for the implemented plain-VADER overlay. The Coverage-Gated design contributes an evidence-breadth mechanism and reduces the Naive Tilt shortfall, but it remains unproven as a return enhancement. The final report should preserve that distinction: the product was built and evaluated, while persistent superiority and sentiment alpha remain unproven.

## References

NLTK Project (2026), *Natural Language Toolkit*, version 3.10.2. Package metadata locally reports name `nltk`, summary `Natural Language Toolkit`, and homepage `https://www.nltk.org/`. [REFERENCE DETAILS REQUIRE STUDENT VERIFICATION]

UNSW FINS3645 (2026), *Financial Market Data Design & Analysis Project Brief*, local file `PROJECT_BRIEF.md`.

UNSW FINS3645 course project_data.zip, accessed through `src/data_access.py`.

VADER sentiment method. [REFERENCE DETAILS REQUIRE STUDENT VERIFICATION]

Markowitz, H. (1952). [REFERENCE DETAILS REQUIRE STUDENT VERIFICATION]

Sharpe, W. F. (1966). [REFERENCE DETAILS REQUIRE STUDENT VERIFICATION]

## Appendix Plan

[INSERT APPENDIX TABLE A1 HERE:
Source file: results/tables/performance_metrics.csv
Purpose: Provide complete fund metrics beyond the selected narrative rows.
Required columns: all columns in the performance metrics artifact.
Proposed caption: Appendix Table A1. Complete performance metrics across all Signal Mosaic funds.
Student interpretation required: No]

[INSERT APPENDIX FIGURE A1 HERE:
Source file: results/figures/fund_weights_over_time_combined.png
Purpose: Show combined-fund weights over time.
Proposed caption: Appendix Figure A1. Combined-fund weights over time by method.
Student interpretation required: Yes]

[INSERT APPENDIX TABLE A2 HERE:
Source file: results/tables/fund_latest_holdings.csv
Purpose: Provide latest target holdings for all funds.
Required columns: fund_name, asset_family, method, asset, asset_class, sector, target_weight.
Proposed caption: Appendix Table A2. Latest target holdings by fund.
Student interpretation required: No]

[INSERT APPENDIX TABLE A3 HERE:
Source file: results/tables/fund_fact_sheet_summary.csv
Purpose: Provide concise fund fact-sheet summary fields.
Required columns: fund_id, fund_name, asset_family, method, first_live_date, end_date, annualised_return_net, annualised_volatility_net, Sharpe_net, maximum_drawdown_net.
Proposed caption: Appendix Table A3. Fund fact-sheet summary.
Student interpretation required: No]

[INSERT APPENDIX TABLE A4 HERE:
Source file: results/tables/sentiment_model_diagnostics.csv
Purpose: Report plain-VADER scoring counts and shares.
Required columns: total_scored_headlines, exact_zero_compound_count, vader_neutral_count, positive_count, negative_count, exact_zero_compound_share, vader_neutral_share, positive_share, negative_share.
Proposed caption: Appendix Table A4. Plain-VADER headline scoring diagnostics.
Student interpretation required: Yes]

[INSERT APPENDIX TABLE A5 HERE:
Source file: results/tables/fusion_predictive_diagnostics.csv
Purpose: Report non-parametric sentiment-return rank-correlation diagnostics.
Required columns: sample, pooled_spearman, average_cross_sectional_spearman, valid_monthly_observations, valid_pair_observations, median_coverage_quality.
Proposed caption: Appendix Table A5. Monthly sentiment-return rank-correlation diagnostics.
Student interpretation required: Yes]

[INSERT APPENDIX TABLE A6 HERE:
Source file: results/tables/pipeline_validation.csv
Purpose: Show reproducibility and app-readiness validation checks.
Required columns: validation_name, expected, observed, status, notes.
Proposed caption: Appendix Table A6. Pipeline validation summary.
Student interpretation required: No]

## Student Review Checklist

### Executive Summary

- Review the interpretation of Crypto Minimum Variance as the strongest headline result.
- Review the statement that sentiment did not improve the equity base fund.
- Review the positioning of Coverage Lens as the main product extension.

### Fund interpretation

- Review the risk-return discussion of crypto funds.
- Review the equity method comparison between Equal Weight, Minimum Variance, and Risk Parity.
- Review the combined-family interpretation of Combined Risk Parity.
- Review the latest-holdings discussion for Combined Minimum Variance.

### Sentiment interpretation

- Review the explanation of VADER-neutral and exact-zero headline shares.
- Confirm that the final wording does not imply VADER understands firm fundamentals.

### Coverage-Gated interpretation

- Review the claim that Coverage-Gated reduced some Naive Tilt damage without creating positive predictive value.
- Confirm that no causal claim is made about coverage causing the return difference.

### Critical reflection

- Review every limitation paragraph in Section 6.
- Decide whether additional project-specific limitations should be added from student experience.

### Recommendations

- Review Recommendation 1 on longer evaluation.
- Review Recommendation 2 on validated sentiment model comparison.
- Review Recommendation 3 on Coverage Lens as disclosure and signal-risk control.

### Product positioning

- Review the statements that fact sheets support investor comparison.
- Review the Allocation Studio positioning as a useful mixed-calendar comparison tool.
- Review the app transparency claim.

