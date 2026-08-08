# Signal Mosaic:
# Systematic Multi-Asset Funds with Coverage-Aware News Sentiment

FINS3645 Financial Market Data Design & Analysis - Project B

Author: Chenhang Huang

zID: z5641844

Term 2, 2026

## Executive Summary

Signal Mosaic is an investment-product prototype built from structured market data and unstructured equity headlines. It offers eleven walk-forward out-of-sample fund histories across equity-only, crypto-only, combined equity-plus-crypto, and equity sentiment-overlay strategies. The data cover 50 US equities, 10 cryptocurrencies, and equity headlines from the UNSW Business School FINS3645 project data bundle (UNSW Business School, 2026). The app and report follow the Data Factory Floor logic of moving from cleaned data to features, models, and a client-facing product (Hric and Lin, 2026).

The backtests use a 2020 initial estimation period, expanding-window estimation, monthly rebalancing, and weights formed before the return period in which they are used. Equity and combined funds run from 2021-01-04 to 2023-12-29; crypto-only funds run from 2021-01-01 to 2023-12-31 on a native seven-day calendar. Sharpe ratios use a risk-free rate of zero (Sharpe, 1966), and net returns include a 10 basis-point one-way turnover-cost assumption after initial establishment.

Crypto Minimum Variance records the highest measured net annualised return and net Sharpe in this sample, at 49.25% and 0.91. This is not a universal "best fund" conclusion because the same fund records 76.12% annualised volatility and a -73.55% maximum drawdown. In the combined family, Combined Risk Parity has the highest net Sharpe at 0.78, while Combined Minimum Variance has the lowest annualised volatility across all funds at 12.72%. No method dominates every metric.

Plain VADER sentiment scores 146,830 aligned equity headlines and produces 10,060 sector-date rows (Hutto and Gilbert, 2014). VADER classifies 49.57% of scored headlines as neutral, and 48.85% receive an exact-zero compound score. These shares indicate a potential false-neutral limitation for finance headlines; they do not show that around half the headlines were economically neutral. Missing-news days remain missing rather than being converted into zero sentiment.

The sentiment-fusion result is negative relative to Equity Equal Weight. Equity Equal Weight records a 12.61% net annualised return and a 0.82 net Sharpe. Equity Naive Sentiment Tilt records 11.65% and 0.77, while Equity Coverage-Gated Sentiment Tilt records 11.91% and 0.78. Coverage-Gated reduces part of the Naive Tilt shortfall but does not beat Equal Weight, so I interpret Coverage Lens as evidence-breadth disclosure and signal-risk control rather than proof of sentiment alpha.

## 1. Funds and Walk-Forward Backtest Design

Signal Mosaic uses three return universes from the UNSW Business School FINS3645 project data bundle. The equity universe contains 50 US equities across ten sectors. The crypto universe contains 10 cryptocurrencies. The combined universe contains all 60 assets, but it is evaluated on the equity trading calendar. Crypto-only returns are computed on the native seven-day calendar and annualised with 365 observations per year. Equity and combined returns are annualised with 252 observations per year (UNSW Business School, 2026).

Table 1 reports the sample and calendar design by family. The initial estimation window is calendar year 2020. For equity and combined funds, usable estimation returns run from 2020-01-03 to 2020-12-31, and the first live return is 2021-01-04. For crypto-only funds, estimation returns run from 2020-01-02 to 2020-12-31, and the first live return is 2021-01-01. The different first-live dates come from the different trading calendars.

At each monthly rebalance date, the optimiser uses returns strictly before that date. The rebalance date is the first available observation of each calendar month. Target weights then apply to that date's return, and weights drift with realised daily returns until the next monthly rebalance. This creates a look-ahead-controlled historical simulation based only on prior information, not live performance.

The base method set is transparent. Equal Weight allocates 1/N across the relevant assets. Minimum Variance solves for long-only, fully invested weights that minimise estimated covariance-based variance, without expected-return estimates (Markowitz, 1952). Risk Parity solves for long-only, fully invested weights that bring asset risk contributions close to equal. Optimised funds use a 20% maximum target weight per asset; Equal Weight remains 1/N.

Net returns include a simple transaction-cost assumption: 10 basis points per dollar of one-way turnover at scheduled rebalances after inception. Turnover is one half of the sum of absolute differences between target and drifted pre-trade weights. The initial establishment trade is not charged. Gross and net histories are retained, but the report uses net results for headline comparisons.

The combined funds use same-date native crypto returns left-joined to the equity calendar. Weekend-only crypto returns are excluded because the combined product is evaluated on equity trading days. Crypto-only funds keep weekend returns on the native seven-day calendar. This distinction matters when comparing families, because the daily observations are not identical across all funds.

## 2. Out-of-Sample Results and Fund Fact Sheets

Table 2 compares the eleven final funds using net annualised return, net annualised volatility, net Sharpe, and maximum drawdown. The nine base funds are Equity Equal Weight, Equity Minimum Variance, Equity Risk Parity, Crypto Equal Weight, Crypto Minimum Variance, Crypto Risk Parity, Combined Equal Weight, Combined Minimum Variance, and Combined Risk Parity. The fusion stage adds Equity Naive Sentiment Tilt and Equity Coverage-Gated Sentiment Tilt. Figure 1 plots the same funds by net return and volatility.

Crypto funds sit at the high-return, high-risk end of Figure 1. Crypto Minimum Variance has the highest measured net annualised return, 49.25%, and the highest net Sharpe ratio, 0.91. Crypto Risk Parity follows with 41.69% and 0.84, while Crypto Equal Weight records 40.41% and 0.83. These results use 1,095 daily observations and a 365-day annualisation factor.

The crypto result must be read with drawdown evidence. Maximum drawdowns are -73.55% for Crypto Minimum Variance, -80.49% for Crypto Risk Parity, and -81.59% for Crypto Equal Weight. Over this sample, crypto dominates the return ranking but not capital preservation. The result is therefore sensitive to how much drawdown risk an investor is willing to accept.

Across the equity base funds, Equal Weight records a 12.61% net annualised return, 16.12% annualised volatility, 0.82 net Sharpe, and -20.26% maximum drawdown. Equity Risk Parity has lower return at 10.04%, lower volatility at 14.93%, a 0.72 net Sharpe, and -19.41% maximum drawdown. Equity Minimum Variance has the lowest equity volatility at 12.73% and the least negative equity drawdown at -17.84%, but its net annualised return is 7.05% and its net Sharpe is 0.60. This is a sample result, not a proven causal mechanism.

The combined family gives a more balanced picture. Combined Equal Weight has the highest combined-family return at 15.08%, with 21.60% volatility, a 0.76 net Sharpe, and -27.90% maximum drawdown. Combined Minimum Variance has 7.05% return, 12.72% volatility, a 0.60 Sharpe, and -17.84% drawdown. Combined Risk Parity has 12.75% return, 17.44% volatility, a 0.78 Sharpe, and -22.40% drawdown, making it the strongest combined fund by net Sharpe. Figure 2 shows the net growth paths by asset family, while Figure 3 focuses on combined-fund drawdowns.

The fund rankings therefore depend on which risk measure is emphasised. A client who only reads the return column would focus on Crypto Minimum Variance, while a client concerned with drawdown would see a much less comfortable result. Within equities, Equal Weight is the cleaner benchmark because it does not add covariance-estimation risk and it keeps each stock at the same strategic weight. In the combined universe, the evidence is more mixed: Equal Weight captures more upside, Minimum Variance cuts risk most visibly, and Risk Parity sits between them with the best combined Sharpe. None of these rankings removes the need to look at turnover, drawdown, and latest backtest target holdings alongside return.

Latest backtest target holdings at the final reported rebalance help explain what each fact sheet represents. Equity Equal Weight holds 50 equities at 2.00% each. Crypto Equal Weight holds 10 cryptocurrencies at 10.00% each. Optimised funds are more concentrated: Equity Minimum Variance has 12 non-zero holdings and a largest weight of 19.82%, Crypto Minimum Variance has 8 and 20.00%, and Combined Minimum Variance has 12 and 19.84%. Combined Minimum Variance's final reported target allocation is 100.00% equity and 0.00% crypto by asset class. That is a final-rebalance observation, not a claim about every rebalance and not an investment recommendation.

Appendix Figure A1 shows how the combined-fund target allocations changed across monthly rebalances. The complete weight history confirms that Combined Minimum Variance kept 0.00% crypto exposure across the combined backtest, Combined Equal Weight kept 16.67% crypto exposure by construction, and Combined Risk Parity held a smaller crypto allocation between 8.38% and 11.83%. The figure is evidence of model exposure through time, not proof that any allocation rule is optimal.

Transaction costs are small in rate terms compared with realised volatility and drawdowns. Total recorded transaction-cost rates range from 0.09% for Equity Risk Parity to 0.24% for Crypto Minimum Variance. Average rebalance turnover ranges from 2.51% for Equity Risk Parity to 6.75% for Crypto Minimum Variance. The sentiment tilts trade more than Equity Equal Weight: average turnover is 4.74% for Coverage-Gated and 5.47% for Naive, compared with 2.65% for Equity Equal Weight.

The fund fact sheets combine growth of one dollar, drawdown, annualised return, annualised volatility, Sharpe ratio, latest backtest target holdings at the final reported rebalance, rebalance assumptions, and transaction-cost assumptions. They make performance, risk, costs, and holdings easier to compare, but they do not provide personal financial advice or decide which fund suits a particular investor.

## 3. Standalone Sector Sentiment Index

The sentiment stage applies plain NLTK VADER 3.10.2 to preserved equity headline text (Hutto and Gilbert, 2014). Each headline is scored on its own. The implementation keeps original casing, punctuation, negation, intensifiers, and word order; it does not lowercase titles, strip punctuation, remove stopwords, or concatenate multiple titles before scoring. Crypto is not scored because the project contains no crypto headline data.

Of the 146,836 deduplicated headline records, 146,830 could be aligned to an available equity trading date and scored. Six end-of-sample records had no later eligible trading date within the sample and were excluded from the aligned sentiment panel. This wording follows the foundation integrity check, which reports six outside-calendar headline rows, and the sentiment scoring function, which drops rows without a mapped trading date before scoring.

Plain VADER classifies 54,980 scored headlines as positive, 72,786 as neutral, and 19,064 as negative using the standard compound-score thresholds. That is 37.44% positive, 49.57% neutral, and 12.98% negative. The exact-zero compound count is 71,720, or 48.85% of scored headlines. I retained plain VADER as the transparent and reproducible baseline rather than changing the model after observing the backtest result. A replacement model should require human-labelled validation and a separate holdout test.

Aggregation happens in two steps. First, headline-level scores are averaged into ticker-day sentiment for each trading date and ticker with at least one headline, creating 37,962 ticker-days. Sector sentiment then equal-weights available ticker-day mean compound scores within each sector. A ticker with 20 headlines still counts as one ticker-day observation, not 20 times the weight of a ticker with one headline.

The sector sentiment artifact uses a complete equity-date-sector grid with 10,060 rows, equal to 1,006 equity trading dates times ten sectors. It contains 9,832 sector-days with news and 228 without news. Missing-news sector-days have raw sentiment left blank rather than filled with zero, so a genuine calculated zero remains distinct from no news. Figure 4 shows the 21-trading-day trailing sector sentiment series.

The timing rule is strict. A raw sector score belongs to the trading day to which headlines are aligned, but it cannot affect that same day's position. If Saturday and Monday headlines both map to Monday, both enter Monday's raw sector index and first become available for Tuesday. This is why the fusion stage uses the one-trading-day-lagged, 21-day trailing sector sentiment measure.

## 4. Innovation: Coverage-Gated Sentiment Fusion

The Signal Mosaic innovation is a coverage-aware sentiment overlay for equity sectors. I retain Equal Weight as the comparison benchmark because it gives each of the ten sectors a 10% strategic weight and each stock within a sector an equal share. This provides the clearest test of the sentiment overlay itself, separate from optimiser-specific sector allocation.

Coverage Lens describes the evidence structure underneath a sector sentiment reading. Coverage share is the fraction of the five sector stocks with headline coverage. Breadth is one divided by five times the sum of squared ticker headline shares within a sector. Breadth near one means headlines are spread more evenly across the five stocks; breadth near 0.2 means one ticker dominates that sector's news coverage. Figure 5 displays sentiment with this coverage context.

Coverage quality is lagged 21-day coverage share multiplied by lagged 21-day breadth. It is not sentiment, and it does not verify whether news is true or predictive. I interpret Coverage Lens mainly as a control on signal confidence and as a disclosure mechanism. Two sectors may have similar sentiment scores but very different evidence breadth.

At each monthly equity rebalance, the fusion stage uses the one-trading-day-lagged, 21-day trailing sector sentiment measure. It standardises sector sentiment across available sectors on that date, clips the z-score to -2 to +2, and applies a fixed alpha of 0.15. If fewer than two sector signals are available, or if cross-sectional variance is zero, the policy applies no active tilt. Missing sector signals are not converted into sentiment zero, and no parameter is retuned after observing the result.

The Naive Sentiment Tilt uses one plus 0.15 times the sector z-score. The Coverage-Gated Sentiment Tilt uses one plus 0.15 times coverage quality times the sector z-score. Coverage inputs are shifted one full equity trading day before use, so coverage attenuates the active view rather than acting as a sentiment score.

The fusion diagnostics contain 360 rebalance-sector observations: 36 monthly rebalances across ten sectors. All 360 have valid sentiment observations. Mean coverage quality is 0.7953, with a minimum of 0.4396 and a maximum of 0.9934. The gate reduces the absolute active tilt in 93.61% of observations. Maximum sector weights are 13.14% for Naive and 12.75% for Coverage-Gated; minimum weights are 6.99% and 7.35%.

Table 3 and Figure 6 show the before-versus-after result. Equity Equal Weight remains strongest among the three comparison funds, with a 12.61% net annualised return, 16.12% net volatility, a 0.82 net Sharpe, -20.26% maximum drawdown, and 42.59% cumulative net return. Equity Naive Sentiment Tilt has 11.65%, 15.97%, 0.77, -20.13%, and 39.00%. Equity Coverage-Gated Sentiment Tilt has 11.91%, 16.00%, 0.78, -20.14%, and 39.98%.

The measured fusion result is negative relative to Equity Equal Weight. Both sentiment tilts reduce net annualised return and net Sharpe. Coverage-Gated does better than Naive by losing less return and Sharpe, which supports the narrower conclusion that coverage attenuation reduced part of the weak signal's damage. It still does not create positive predictive value. I do not treat the negative fusion result as evidence that sentiment can never work; it only shows that this plain-VADER, fixed-alpha, fixed-sample design did not produce a positive predictive relationship.

The predictive diagnostics are consistent with that interpretation. Monthly sector sentiment z-scores are compared with next-rebalance-period sector returns. The pooled Spearman correlation is -0.0705 for all valid observations, -0.0398 above median coverage quality, and -0.0992 at or below median coverage quality. No formal significance claim is made.

## 5. Signal Mosaic App and Investor Journey

The Streamlit app is a presentation and interaction layer over precomputed artifacts. Its six sections are Overview, Compare Funds, Fund Fact Sheet, Allocation Studio, Sentiment & Coverage, and Methodology & Limitations. It reads committed CSV artifacts from the results folder, validates schemas, caches CSV loading, and uses project-relative paths. It does not rerun the analytical pipeline.

The Overview page reports the fund count, sector count, out-of-sample window, validation count, fund shelf, and evidence highlights. Compare Funds lets a user filter, select two to six funds, compare net metrics, view growth of one dollar, risk-return position, Sharpe, and drawdown, and download the comparison table. Fund Fact Sheet shows performance cards, growth, drawdown, latest backtest target holdings at the final reported rebalance, method summary, and downloads.

Allocation Studio is an illustrative fund-of-funds view, not a twelfth managed fund. The user selects two to five precomputed funds and enters weights. The app normalises non-zero weights to 100%, compounds each selected fund's daily net returns within each calendar month, aligns funds on their shared monthly sample, and calculates a monthly rebalanced allocation. Metrics use 12 periods per year and no extra allocation-level transaction cost. This monthly design avoids pretending that equity-calendar and crypto-calendar daily returns line up perfectly.

The Sentiment & Coverage page lets users choose sectors, date ranges, and sentiment views. It shows VADER compound sentiment with a zero reference, then displays article count, covered tickers, coverage share, and breadth separately. It also reports the plain-VADER neutral share and the fusion result. Methodology & Limitations explains the Data Factory Floor, fund design, sentiment design, Coverage-Gated innovation, and pipeline status.

The deployment architecture is intentionally light. The app does not load raw data, call the data-access helper, run build scripts, execute the pipeline, import NLTK, initialise VADER, optimise portfolios, rebuild sentiment or fusion, write analytical files, or depend on Project A. Pipeline validation reports 81 PASS rows, and the app artifact inventory reports nine ready app-facing artifacts. Signal Mosaic keeps fund performance, holdings, sentiment, coverage, methodology, and limitations visible in one journey, but it remains an educational prototype rather than financial advice.

## 6. Critical Reflection and Three Recommendations

The test window is short. Equity and combined funds have 753 out-of-sample observations from 2021-01-04 to 2023-12-29, while crypto-only funds have 1,095 observations from 2021-01-01 to 2023-12-31. The project measures one historical period, not a stable long-run distribution, and the universe is limited to 50 large US equities and 10 cryptocurrencies with no external validation dataset.

The sentiment evidence is narrower than the fund evidence. It uses headlines only, not full article text, and applies only to equities because there is no crypto headline dataset. Plain VADER is transparent and reproducible, but it leaves 49.57% of scored headlines neutral and 48.85% as exact-zero compound scores. That creates false-neutral risk for finance headlines.

Portfolio implementation is simplified. The transaction-cost model charges 10 basis points per dollar of one-way turnover, excludes initial establishment cost, and does not model taxes, market impact, custody, management fees, borrow costs, liquidity constraints, or trade-size effects.

Calendar choices also matter. Combined funds exclude weekend-only crypto returns because they use the equity calendar, while crypto-only funds keep the seven-day calendar. This is internally consistent, but the combined fund is not the same as a continuously traded crypto allocation. Allocation Studio handles mixed calendars with common monthly returns rather than artificial daily alignment.

Coverage Lens should be treated as evidence structure, not truth. It measures whether headlines are broad or concentrated across the sector, but it does not verify news, measure article quality, or prove predictability. Since fusion diagnostics are negative in this sample, coverage is better framed as signal-risk control and disclosure.

Recommendation 1 is to extend evaluation before commercial use. The next version should test a longer out-of-sample history, additional market regimes, multiple-origin or rolling validation, stress periods, frozen parameters, transaction-cost sensitivity, and separate checks of crypto-calendar assumptions.

Recommendation 2 is to improve sentiment only through validated model comparison. Plain VADER should remain the transparent baseline. A finance lexicon or finance-specific model should be compared against a manually labelled finance-headline sample and a separate holdout period. The comparison should measure positive, negative, and neutral classification quality, and no model should be selected merely because it raises backtest return.

Recommendation 3 is to use Coverage Lens mainly as signal-risk control and disclosure. The app should show coverage beside sentiment, preserve missing-news warnings, and attenuate active tilts when evidence is narrow. Equal Weight should remain the transparent default until a sentiment overlay produces positive and stable out-of-sample evidence. Coverage should not be marketed as predictive proof.

## 7. Conclusion

Signal Mosaic builds the required Part B analytical product: eleven out-of-sample funds, validated fund fact sheets, a standalone equity-sector sentiment index, a look-ahead-safe sentiment fusion extension, and a Streamlit app that loads precomputed artifacts. The pipeline validation table reports 81 PASS rows, and the app artifact inventory reports nine ready app-facing artifacts.

The fund evidence is mixed. Crypto Minimum Variance leads return and Sharpe rankings but has a large drawdown. Combined Risk Parity is the strongest combined fund by Sharpe. Equity Equal Weight remains stronger than both sentiment overlays in the fusion comparison.

The sentiment evidence does not show positive predictive value for the implemented plain-VADER overlay. Coverage-Gated adds a coverage-aware control on signal size and reduces some of the Naive Tilt shortfall, but it remains unproven as a return enhancement. The product was built and evaluated; persistent superiority and sentiment alpha remain unproven.

## References

Hric, J. and Lin, Y. (2026) Applied Data Science in FinTech: Models, Tools, and Case Studies. London: Routledge.

Hutto, C.J. and Gilbert, E.E. (2014) 'VADER: A Parsimonious Rule-Based Model for Sentiment Analysis of Social Media Text', Proceedings of the International AAAI Conference on Web and Social Media, 8(1), pp. 216-225.

Markowitz, H. (1952) 'Portfolio Selection', The Journal of Finance, 7(1), pp. 77-91.

Sharpe, W.F. (1966) 'Mutual Fund Performance', The Journal of Business, 39(1, Part 2), pp. 119-138.

UNSW Business School (2026) FINS3645 Project Data Bundle: project_data.zip [dataset].

## Appendices

Appendix Table A1 reports expanded performance and implementation metrics for all eleven funds.

Appendix Figure A1 shows combined-fund target allocations over monthly rebalances.

Appendix Table A2 reports representative latest backtest target holdings at the final reported rebalance.

Appendix Table A3 reports the fund fact-sheet summary.

Appendix Table A4 reports plain-VADER sentiment diagnostics.

Appendix Table A5 reports the monthly sentiment-return rank-correlation diagnostics. No formal significance claim is made.

Appendix Table A6 summarises pipeline validation. The complete validation table is included in the submitted project artifacts.
