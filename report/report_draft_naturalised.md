# Signal Mosaic:
# Systematic Multi-Asset Funds with Coverage-Aware News Sentiment

**FINS3645 Financial Market Data Design & Analysis - Project B**

## DRAFT FOR STUDENT REVIEW

This Phase 1 revised draft keeps the verified evidence from `report/report_draft.md` but rewrites the prose in a more natural student voice. Marked paragraphs still require student review before any Word or PDF submission is produced.

This notice belongs to the Markdown draft only. It is not intended to appear automatically in the final submitted report.

## Executive Summary

Signal Mosaic is an investment-product prototype built from structured market data and unstructured equity headlines. It offers eleven walk-forward out-of-sample fund histories across equity-only, crypto-only, combined equity-plus-crypto, and equity sentiment-overlay strategies. The data cover 50 US equities across ten sectors, 10 cryptocurrencies, and equity headlines scored with plain VADER.

The backtests use a 2020 initial estimation period, expanding-window estimation, monthly rebalancing, and weights formed before the return period in which they are used. Equity and combined funds run from 2021-01-04 to 2023-12-29. Crypto-only funds run from 2021-01-01 to 2023-12-31 on the native seven-day calendar. Sharpe ratios use a risk-free rate of zero. Net returns include a 10 basis-point one-way turnover-cost assumption after initial establishment.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The highest measured net return and Sharpe result is Crypto Minimum Variance, with a 49.25% net annualised return and a 0.91 net Sharpe ratio. That is not a simple "best fund" conclusion because the same fund records 76.12% annualised volatility and a -73.55% maximum drawdown. In the combined family, Combined Risk Parity has the highest net Sharpe at 0.78, while Combined Minimum Variance has the lowest annualised volatility across all funds at 12.72%.

The standalone sentiment index scores 146,830 valid equity headlines and produces 10,060 date-sector rows. Plain VADER classifies 49.57% of scored headlines as neutral, and 48.85% receive an exact-zero compound score. No-news sector-days remain missing rather than being converted into neutral sentiment. Every investable sentiment field is lagged by at least one complete trading day.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The sentiment-fusion result is cautious. Equity Equal Weight records a 12.61% net annualised return and a 0.82 net Sharpe. Equity Naive Sentiment Tilt records 11.65% and 0.77, while Equity Coverage-Gated Sentiment Tilt records 11.91% and 0.78. Coverage-Gated reduces part of the Naive Tilt shortfall, but it does not beat Equal Weight. The pooled sentiment-return Spearman correlation remains negative at -0.0705.

[STUDENT REVIEW REQUIRED — Product positioning]

Coverage Lens is the main Signal Mosaic product extension. It does not verify whether a news signal is true or predictive. Its narrower role is to show whether sector sentiment rests on broad headline coverage or a concentrated set of headlines around only a few stocks.

## 1. Funds and Walk-Forward Backtest Design

Signal Mosaic uses three return universes. The equity universe contains 50 US equities across ten sectors. The crypto universe contains 10 cryptocurrencies. The combined universe contains all 60 assets, but it is evaluated on the equity trading calendar. Crypto-only returns are computed on the native seven-day calendar and annualised with 365 observations per year. Equity and combined returns are annualised with 252 observations per year.

The initial estimation window is calendar year 2020. For equity and combined funds, usable estimation returns run from 2020-01-03 to 2020-12-31, and the first live return is 2021-01-04. For crypto-only funds, estimation returns run from 2020-01-02 to 2020-12-31, and the first live return is 2021-01-01.

[INSERT TABLE 1 HERE:
Source file: results/tables/fund_backtest_design.csv
Purpose: Document sample dates, calendars, annualisation, window type, rebalance rule, training rule, constraints, risk-free-rate assumption, and transaction-cost assumption.
Required columns: fund_name, asset_family, method, calendar, annualisation_factor, initial_estimation_start, initial_estimation_end, first_live_date, end_date, window_type, rebalance_rule, training_rule, holding_rule, max_target_weight, risk_free_rate, transaction_cost_rate.
Proposed caption: Table 1. Walk-forward backtest design and assumptions by fund family and method.
Student interpretation required: No]

At each monthly rebalance date, the optimiser uses returns strictly before that date. The rebalance date is the first available observation of each calendar month. Target weights then apply to that date's return, and weights drift with realised daily returns until the next monthly rebalance.

The base method set is deliberately transparent. Equal Weight allocates 1/N across the relevant assets. Minimum Variance solves for long-only, fully invested weights that minimise estimated covariance-based variance, without expected-return estimates. Risk Parity solves for long-only, fully invested weights that bring asset risk contributions close to equal. Optimised funds use a 20% maximum target weight per asset; Equal Weight remains 1/N.

Net returns include a simple transaction-cost assumption: 10 basis points per dollar of one-way turnover at scheduled rebalances after inception. Turnover is one half of the sum of absolute differences between target and drifted pre-trade weights. The initial establishment trade is not charged. Gross and net histories are retained, but the report uses net results for headline comparisons.

The combined funds use same-date native crypto returns left-joined to the equity calendar. Weekend-only crypto returns are excluded because the combined product is evaluated on equity trading days. Crypto-only funds keep weekend returns on the native seven-day calendar.

[STUDENT REVIEW REQUIRED — Economic interpretation]

This design gives a look-ahead-controlled historical simulation based only on prior information. It is not live performance. It also does not show that the same fund rankings would hold outside 2021-2023.

## 2. Out-of-Sample Results and Fund Fact Sheets

The final performance metrics table contains eleven funds. The nine base funds are Equity Equal Weight, Equity Minimum Variance, Equity Risk Parity, Crypto Equal Weight, Crypto Minimum Variance, Crypto Risk Parity, Combined Equal Weight, Combined Minimum Variance, and Combined Risk Parity. The fusion stage adds Equity Naive Sentiment Tilt and Equity Coverage-Gated Sentiment Tilt. The main report table should show Fund, Family, Net annualised return, Net volatility, Net Sharpe, and Maximum drawdown; turnover, cost, holding-count, and largest-weight fields can sit in the appendix.

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

Crypto funds sit at the high-return, high-risk end of Figure 1. Crypto Minimum Variance has the highest net annualised return, 49.25%, and the highest net Sharpe ratio, 0.91. Crypto Risk Parity follows with 41.69% and 0.84, while Crypto Equal Weight records 40.41% and 0.83. These results use 1,095 daily observations and a 365-day annualisation factor.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The crypto result needs to be read with the drawdown evidence. Maximum drawdowns are -73.55% for Crypto Minimum Variance, -80.49% for Crypto Risk Parity, and -81.59% for Crypto Equal Weight. Over this sample, crypto dominates the return ranking but not capital preservation, so the result is sensitive to how much drawdown risk an investor is willing to bear.

Across the equity base funds, Equal Weight records a 12.61% net annualised return, 16.12% annualised volatility, 0.82 net Sharpe, and -20.26% maximum drawdown. Equity Risk Parity has lower return at 10.04%, lower volatility at 14.93%, a 0.72 net Sharpe, and -19.41% maximum drawdown. Equity Minimum Variance has the lowest equity volatility at 12.73% and the least negative equity drawdown at -17.84%, but its net annualised return is 7.05% and its net Sharpe is 0.60.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The equity comparison shows the main risk-control trade-off in the sample. Minimum Variance reduces volatility and drawdown, but it gives up return. Equal Weight keeps broader equity exposure and has the strongest equity Sharpe here. The backtest does not establish why this pattern occurred or whether it would persist in another period.

The combined family gives a more balanced picture. Combined Equal Weight has the highest combined-family return at 15.08%, with 21.60% volatility, a 0.76 net Sharpe, and -27.90% maximum drawdown. Combined Minimum Variance has 7.05% return, 12.72% volatility, a 0.60 Sharpe, and -17.84% drawdown. Combined Risk Parity has 12.75% return, 17.44% volatility, a 0.78 Sharpe, and -22.40% drawdown, making it the strongest combined fund by net Sharpe.

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

Holdings at the final reported rebalance help explain what each fact sheet represents. Equity Equal Weight holds 50 equities at 2.00% each. Crypto Equal Weight holds 10 cryptocurrencies at 10.00% each. Optimised funds are more concentrated: Equity Minimum Variance has 12 non-zero holdings and a largest weight of 19.82%, Crypto Minimum Variance has 8 and 20.00%, and Combined Minimum Variance has 12 and 19.84%. Its final target allocation is 100.00% equity and 0.00% crypto by asset class.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The final Combined Minimum Variance holdings show no material crypto allocation at the last rebalance. That is a holdings-based observation, not a claim that the fund avoided crypto at every rebalance and not a recommendation to exclude crypto.

Appendix Figure A1 should show `results/figures/fund_weights_over_time_combined.png`. It gives a time-series view of combined-fund allocations by method, while the latest-holdings table reports only the final rebalance. The distinction matters because a final snapshot cannot show whether an allocation pattern was stable through the backtest.

Transaction costs are small in rate terms compared with realised volatility and drawdowns. Total recorded transaction-cost rates range from 0.09% for Equity Risk Parity to 0.24% for Crypto Minimum Variance. Average rebalance turnover ranges from 2.51% for Equity Risk Parity to 6.75% for Crypto Minimum Variance. The sentiment tilts trade more than Equity Equal Weight: average turnover is 4.74% for Coverage-Gated and 5.47% for Naive, compared with 2.65% for Equity Equal Weight.

Each fund fact sheet shows growth of one dollar, drawdown, annualised return, annualised volatility, Sharpe ratio, holdings at the final reported rebalance, rebalance assumptions, and transaction-cost assumptions. Useful examples are Equity Equal Weight as the transparent equity base, Crypto Minimum Variance as the highest measured net return and Sharpe fund, Combined Risk Parity as the strongest combined fund by Sharpe, and Equity Coverage-Gated Sentiment Tilt as the Signal Mosaic innovation fund.

[STUDENT REVIEW REQUIRED — Product positioning]

The fact-sheet format makes performance, risk, costs, and holdings easier to compare. It still does not provide personal financial advice or decide which fund suits a particular investor.

## 3. Standalone Sector Sentiment Index

The sentiment stage applies plain NLTK VADER to preserved equity headline text. Each headline is scored on its own. The implementation keeps original casing, punctuation, negation, intensifiers, and word order; it does not lowercase titles, strip punctuation, remove stopwords, or concatenate multiple titles before scoring. Crypto is not scored because the project contains no crypto headline data.

The cleaned headline set contains 146,836 rows. Of these, 146,830 enter the scored and trading-day-aligned sentiment panel. The six excluded records are explained by the foundation integrity check: six end-of-sample headlines fall outside the available equity trading calendar after same-or-next trading-day alignment. The scoring function also excludes missing or empty titles, but the local counts show that the observed six-record difference is the outside-calendar case.

Plain VADER classifies 54,980 scored headlines as positive, 72,786 as neutral, and 19,064 as negative using the standard compound-score thresholds. That is 37.44% positive, 49.57% neutral, and 12.98% negative. The exact-zero compound count is 71,720, or 48.85% of scored headlines.

[STUDENT REVIEW REQUIRED — Critical reflection]

The neutral share should not be treated as proof that half the news has no economic content. The local data guide warns that headline sentiment is a noisy proxy, and general-purpose VADER can miss finance-specific tone. I keep plain VADER as the transparent baseline here rather than changing the model after seeing the backtest.

Aggregation happens in two steps. First, headline-level scores are averaged into ticker-day sentiment for each trading date and ticker with at least one headline, creating 37,962 ticker-days. Sector sentiment then equal-weights available ticker-day mean compound scores within each sector. A ticker with 20 headlines still counts as one ticker-day observation, not 20 times the weight of a ticker with one headline.

The sector sentiment artifact uses a complete equity-date-sector grid with 10,060 rows, equal to 1,006 equity trading dates times ten sectors. It contains 9,832 sector-days with news and 228 without news. Missing-news sector-days have raw sentiment left blank rather than filled with zero, so a genuine calculated zero remains distinct from no news. The artifact also includes one-trading-day lagged raw sentiment, 21-trading-day trailing sentiment, and a lagged 21-trading-day trailing measure.

[INSERT FIGURE 4 HERE:
Source file: results/figures/sector_sentiment_timeseries.png
Purpose: Show 21-trading-day trailing sector sentiment across the ten equity sectors.
Proposed caption: Figure 4. Plain-VADER sector sentiment over time, headline-aligned dates.
Student interpretation required: Yes]

The timing rule is strict. A raw sector score belongs to the trading day to which headlines are aligned, but it cannot affect that same day's position. If Saturday and Monday headlines both map to Monday, both enter Monday's raw sector index and first become available for Tuesday.

Coverage fields reconcile with the foundation coverage panel. For each sector-date, the artifact includes article count, covered tickers, coverage share, breadth, and a news flag, so sentiment can be read beside the amount and breadth of supporting headline coverage.

## 4. Innovation: Coverage-Gated Sentiment Fusion

The Signal Mosaic innovation is a coverage-aware sentiment overlay for equity sectors. I retain Equal Weight as the comparison base because it gives each of the ten sectors a 10% strategic weight and each stock within a sector an equal share. This provides the clearest test of the sentiment overlay itself, separate from optimiser-specific sector allocation.

Coverage share is covered sector tickers divided by five. Breadth is one divided by five times the sum of squared ticker headline shares within a sector. Breadth near one means headlines are spread more evenly across the five stocks; breadth near 0.2 means one ticker dominates that sector's news coverage.

[STUDENT REVIEW REQUIRED — Product positioning]

I interpret Coverage Lens mainly as a way to disclose signal support, not as a separate return predictor. Two sectors may have similar sentiment scores but very different headline breadth.

[INSERT FIGURE 5 HERE:
Source file: results/figures/sentiment_coverage_context.png
Purpose: Display sector sentiment together with coverage context.
Proposed caption: Figure 5. Sector sentiment with Coverage Lens context.
Student interpretation required: Yes]

At each monthly equity rebalance, the fusion stage uses the one-trading-day-lagged, 21-day trailing sector sentiment measure. It standardises sector sentiment across available sectors on that date, clips the z-score to -2 to +2, and applies a fixed alpha of 0.15. If fewer than two sector signals are available, or if cross-sectional variance is zero, the policy applies no active tilt. Missing sector signals are not converted into sentiment zero.

The Naive Sentiment Tilt uses one plus 0.15 times the sector z-score. The Coverage-Gated Sentiment Tilt uses one plus 0.15 times coverage quality times the sector z-score. Coverage quality is lagged 21-day coverage share multiplied by lagged 21-day breadth. Coverage inputs are shifted one full equity trading day before use, so coverage attenuates the active view rather than acting as a sentiment score.

The fusion diagnostics contain 360 rebalance-sector observations: 36 monthly rebalances across ten sectors. All 360 have valid sentiment observations. Mean coverage quality is 0.7953, with a minimum of 0.4396 and a maximum of 0.9934. The gate reduces the absolute active tilt in 93.61% of observations. Maximum sector weights are 13.14% for Naive and 12.75% for Coverage-Gated; minimum weights are 6.99% and 7.35%.

[INSERT TABLE 3 HERE:
Source file: results/tables/fusion_before_after.csv
Purpose: Compare Equity Equal Weight, Equity Naive Sentiment Tilt, and Equity Coverage-Gated Sentiment Tilt.
Required columns: fund_name, annualised_return_net, annualised_volatility_net, Sharpe_net, maximum_drawdown_net, cumulative_return_net, average_rebalance_turnover, total_transaction_cost, number_of_rebalances, change_in_return_vs_base, change_in_volatility_vs_base, change_in_Sharpe_vs_base, change_in_max_drawdown_vs_base.
Proposed caption: Table 3. Before-versus-after sentiment fusion results.
Student interpretation required: Yes]

Equity Equal Weight remains strongest among the three comparison funds. It has a 12.61% net annualised return, 16.12% net volatility, a 0.82 net Sharpe, -20.26% maximum drawdown, and 42.59% cumulative net return. Equity Naive Sentiment Tilt has 11.65%, 15.97%, 0.77, -20.13%, and 39.00%. Equity Coverage-Gated Sentiment Tilt has 11.91%, 16.00%, 0.78, -20.14%, and 39.98%.

[INSERT FIGURE 6 HERE:
Source file: results/figures/fusion_growth_of_one.png
Purpose: Show net growth of one dollar for Equity Equal Weight, Naive Sentiment Tilt, and Coverage-Gated Sentiment Tilt.
Proposed caption: Figure 6. Equity Equal Weight versus sentiment-overlay growth of one dollar.
Student interpretation required: Yes]

[STUDENT REVIEW REQUIRED — Economic interpretation]

The measured fusion result is negative relative to Equity Equal Weight. Both sentiment tilts reduce net annualised return and net Sharpe. Coverage-Gated does better than Naive by losing less return and Sharpe, but it still does not beat the base fund. I do not treat this as proof that sentiment can never work; the narrower conclusion is that this fixed plain-VADER overlay did not improve the equity base fund in the 2021-2023 test.

The predictive diagnostics compare monthly sector sentiment z-scores with next-rebalance-period sector returns. The pooled Spearman correlation is -0.0705 for all valid observations. Above median coverage quality, the pooled Spearman correlation is -0.0398. At or below median coverage quality, it is -0.0992. Average cross-sectional monthly Spearman correlations are also negative in all three samples. The median coverage split is descriptive only; it was not used to retune alpha or choose a threshold.

[STUDENT REVIEW REQUIRED — Economic interpretation]

These rank correlations do not support a positive predictive relationship in this sample. They do not prove that sentiment is useless in every setting. They show that this particular plain-VADER, fixed-alpha, coverage-gated design did not provide positive predictive evidence over the observed period.

## 5. Signal Mosaic App and Investor Journey

The Streamlit app is a presentation and interaction layer over precomputed artifacts. Its six sections are Overview, Compare Funds, Fund Fact Sheet, Allocation Studio, Sentiment & Coverage, and Methodology & Limitations. It reads committed CSV artifacts from the results folder, validates schemas, caches CSV loading, and uses project-relative paths.

The Overview page reports the fund count, sector count, out-of-sample window, validation count, fund shelf, and evidence highlights. Compare Funds lets a user filter, select two to six funds, compare net metrics, view growth of one dollar, risk-return position, Sharpe, and drawdown, and download the comparison table. Fund Fact Sheet shows performance cards, growth, drawdown, holdings at the final reported rebalance, method summary, and downloads.

Allocation Studio is an illustrative fund-of-funds view, not a twelfth managed fund. The user selects two to five precomputed funds and enters weights. The app normalises non-zero weights to 100%, compounds each selected fund's daily net returns within each calendar month, aligns funds on their shared monthly sample, and calculates a monthly rebalanced allocation. Metrics use 12 periods per year and no extra allocation-level transaction cost.

[STUDENT REVIEW REQUIRED — Product positioning]

The monthly allocation design avoids pretending that equity-calendar and crypto-calendar daily returns line up perfectly. It compares selected funds on a common monthly basis without interpolating daily returns or rebuilding any fund model.

The Sentiment & Coverage page lets users choose sectors, date ranges, and sentiment views. It shows VADER compound sentiment with a zero reference, then displays article count, covered tickers, coverage share, and breadth separately. It also reports the plain-VADER neutral share and the fusion result. Methodology & Limitations explains the Data Factory Floor, fund design, sentiment design, Coverage-Gated innovation, and pipeline status.

The deployment architecture is intentionally light. The app does not load raw data, call the data-access helper, run build scripts, execute the pipeline, import NLTK, initialise VADER, optimise portfolios, rebuild sentiment or fusion, write analytical files, or depend on Project A. Pipeline validation reports 81 PASS rows, and the app artifact inventory reports nine ready app-facing artifacts.

[STUDENT REVIEW REQUIRED — Product positioning]

Signal Mosaic keeps fund performance, holdings, sentiment, coverage, methodology, and limitations visible in one user journey. That is a transparency claim about the prototype, not a claim that the app gives personal advice or predicts future returns.

## 6. Critical Reflection and Three Recommendations

[STUDENT REVIEW REQUIRED — Critical reflection]

The test window is short. Equity and combined funds have 753 out-of-sample observations from 2021-01-04 to 2023-12-29, while crypto-only funds have 1,095 observations from 2021-01-01 to 2023-12-31. The project measures one historical period, not a stable long-run distribution. The universe is also limited to 50 large US equities and 10 cryptocurrencies, with no external validation dataset in the local project.

[STUDENT REVIEW REQUIRED — Critical reflection]

The sentiment evidence is narrower than the fund evidence. It uses headlines only, not full article text, and applies only to equities because there is no crypto headline dataset. Plain VADER is transparent and reproducible, but it leaves 49.57% of scored headlines neutral and 48.85% as exact-zero compound scores. That creates false-neutral risk for finance headlines.

[STUDENT REVIEW REQUIRED — Critical reflection]

Portfolio implementation is simplified. The transaction-cost model charges 10 basis points per dollar of one-way turnover, excludes initial establishment cost, and does not model taxes, market impact, custody, management fees, borrow costs, liquidity constraints, or trade-size effects. Those omissions matter if the prototype is read as a real investment product rather than a coursework simulation.

[STUDENT REVIEW REQUIRED — Critical reflection]

Calendar choices also matter. Combined funds exclude weekend-only crypto returns because they use the equity calendar, while crypto-only funds keep the seven-day calendar. This is internally consistent, but the combined fund is not the same as a continuously traded crypto allocation. Allocation Studio handles mixed calendars with common monthly returns rather than artificial daily alignment.

[STUDENT REVIEW REQUIRED — Critical reflection]

Coverage Lens should be treated as evidence structure, not truth. It measures whether headlines are broad or concentrated across the sector, but it does not verify news, measure article quality, or prove predictability. Since fusion diagnostics are negative in this sample, coverage is better framed as signal-risk control and disclosure.

[STUDENT REVIEW REQUIRED — Recommendation]

Recommendation 1 - Extend evaluation before commercial use. The next version should test a longer out-of-sample period, more market regimes, rolling or multiple-origin validation, stress periods, frozen parameter decisions, transaction-cost sensitivity, and separate validation of the crypto calendar assumptions. This follows directly from the short 2021-2023 window and the severe crypto drawdowns.

[STUDENT REVIEW REQUIRED — Recommendation]

Recommendation 2 - Improve sentiment only through validated model comparison. Plain VADER should remain the transparent baseline. A finance lexicon or finance-specific model should be compared against a manually labelled representative headline sample and a separate holdout period. The comparison should test neutral, positive, and negative classification quality. A new model should not be chosen only because it improves the backtest.

[STUDENT REVIEW REQUIRED — Recommendation]

Recommendation 3 - Use Coverage Lens primarily as signal-risk control and disclosure. The app should continue to display coverage beside sentiment, preserve missing-news warnings, and attenuate active tilts when coverage is narrow. Equal Weight should remain the transparent default until a sentiment overlay produces positive out-of-sample evidence. Coverage should not be marketed as predictive proof.

## 7. Conclusion

Signal Mosaic builds the required Part B analytical product: eleven out-of-sample funds, validated fund fact sheets, a standalone equity-sector sentiment index, a look-ahead-safe sentiment fusion extension, and a Streamlit app that loads precomputed artifacts. The pipeline validation table reports 81 PASS rows, and the app artifact inventory reports nine ready app-facing artifacts.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The fund evidence is mixed. Crypto Minimum Variance leads return and Sharpe rankings but has a large drawdown. Combined Risk Parity is the strongest combined fund by Sharpe. Equity Equal Weight remains stronger than both sentiment overlays in the fusion comparison.

[STUDENT REVIEW REQUIRED — Economic interpretation]

The sentiment evidence does not show positive predictive value for the implemented plain-VADER overlay. Coverage-Gated adds a coverage-aware control on signal size and reduces some of the Naive Tilt shortfall, but it remains unproven as a return enhancement. The product was built and evaluated; persistent superiority and sentiment alpha remain unproven.

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

- Review the interpretation of Crypto Minimum Variance as the highest measured net return and Sharpe result.
- Review the statement that sentiment did not improve the equity base fund.
- Review the positioning of Coverage Lens as the main product extension.

### Fund interpretation

- Review the risk-return discussion of crypto funds.
- Review the equity method comparison between Equal Weight, Minimum Variance, and Risk Parity.
- Review the combined-family interpretation of Combined Risk Parity.
- Review the final-rebalance holdings discussion for Combined Minimum Variance.

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
