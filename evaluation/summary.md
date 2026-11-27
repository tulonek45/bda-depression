# Model evaluation

## 1. Convergence

Targets: R-hat <= 1.01, ESS >= 400, no divergences or max tree depth hits.

```
model  max_r_hat  min_ess_bulk  min_ess_tail  divergences  max_treedepth_hits
   M0   1.001299   3047.888621   2675.306265            0                   0
   M1   1.002834   4975.490444   3244.725257            0                   0
   M2   1.003019   1411.180500   1803.563023            0                   0
```

## 2. Posterior predictive checks: subgroups outside the 90% interval

About 1 in 10 groups falls outside by chance.

```
model          variable   group    n  observed  rep_q05  rep_q95  outside_90
   M0           smoking current  666  0.228228 0.132132 0.181682        True
   M0           smoking   never 2796  0.118741 0.122318 0.148426        True
   M0 vigorous_activity      no 2441  0.154445 0.117554 0.145023        True
   M0 vigorous_activity     yes 2216  0.108303 0.119585 0.148014        True
   M0             sleep     <6h  360  0.261111 0.110972 0.172222        True
   M0             sleep    6-7h  561  0.169340 0.108734 0.158645        True
   M0             sleep    7-8h 1314  0.103501 0.108828 0.142314        True
   M0             sleep    8-9h 1479  0.091278 0.110176 0.139959        True
   M0           alcohol  >14/wk  318  0.163522 0.088050 0.144654        True
```

## 2. Posterior predictive checks: survey clusters

About 3 of 30 clusters fall outside by chance. ppp_sd near 0 means the model under-predicts how much the rate varies between clusters.

```
model  clusters_outside_90  n_clusters  observed_sd  replicated_sd_mean  ppp_sd
   M0                    3          30     0.035097            0.034670   0.464
   M1                    2          30     0.035097            0.035534   0.514
   M2                    0          30     0.035097            0.037532   0.681
```

## 3. PSIS-LOO

Pareto k > 0.7 would make LOO unreliable.

```
   model     elpd_loo        se     p_loo  max_pareto_k  n_pareto_k_gt_0.7
      M0 -1706.761737 42.260350  3.818800      0.157449                0.0
      M1 -1640.851160 42.079715 11.202851      0.277898                0.0
      M2 -1641.157959 42.102690 17.089912      0.274873                0.0
baseline -1822.308999       NaN       NaN           NaN                NaN
```

## 3. Pairwise elpd differences

Clear when |elpd_diff| > 4 and > 2 SE. M1 - M0: do habits help? M2 - M1: do clusters help?

```
   comparison  elpd_diff        se  clear
M0 - baseline 115.547263 14.616856   True
      M1 - M0  65.910576 12.289321   True
      M2 - M1  -0.306799  1.143368  False
```

## 3. az.compare



```
model  rank  elpd_diff  dse  p_worse       diag_diff  diag_elpd    p    elpd   se  weight
   M1     0        0.0  0.0      NaN             NaN        NaN 11.2 -1640.0 42.0    0.70
   M2     1       -0.0  1.1     0.61 |elpd_diff| < 4        NaN 17.1 -1640.0 42.0    0.27
   M0     2      -70.0 12.0     1.00             NaN        NaN  3.8 -1710.0 42.0    0.03
```

## 4. Prior sensitivity: posterior means by prior scale

Shifts above about 0.5 posterior SD are worth discussing.

```
model                term    0.5    1.0    2.0  max_abs_shift_in_sd
   M1     I(sleep_c ** 2)  0.058  0.059  0.059                0.140
   M1           Intercept -2.329 -2.377 -2.392                0.470
   M1               age_z -0.441 -0.466 -0.474                0.502
   M1           alcohol_z  0.091  0.092  0.092                0.043
   M1       gender_female  0.410  0.459  0.472                0.517
   M1            income_z -0.407 -0.405 -0.404                0.036
   M1         sedentary_z  0.162  0.163  0.163                0.014
   M1             sleep_c -0.114 -0.116 -0.117                0.069
   M1     smoking_current  0.444  0.523  0.549                0.675
   M1      smoking_former  0.080  0.126  0.142                0.391
   M1        vigorous_act -0.384 -0.425 -0.437                0.416
   M2 1|stratum_psu_sigma  0.105  0.112  0.111                0.106
   M2     I(sleep_c ** 2)  0.058  0.059  0.060                0.123
   M2           Intercept -2.332 -2.378 -2.398                0.417
   M2               age_z -0.442 -0.466 -0.473                0.464
   M2           alcohol_z  0.090  0.092  0.092                0.053
   M2       gender_female  0.408  0.455  0.470                0.482
   M2            income_z -0.406 -0.406 -0.406                0.007
   M2         sedentary_z  0.161  0.164  0.164                0.065
   M2             sleep_c -0.116 -0.117 -0.117                0.050
   M2     smoking_current  0.443  0.523  0.548                0.666
   M2      smoking_former  0.082  0.123  0.140                0.354
   M2        vigorous_act -0.385 -0.425 -0.434                0.410
```
