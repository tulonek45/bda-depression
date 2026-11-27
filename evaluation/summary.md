# Model evaluation

## 1. Convergence

Targets: R-hat <= 1.01, ESS >= 400, no divergences or max tree depth hits.

```
model  max_r_hat  min_ess_bulk  min_ess_tail  divergences  max_treedepth_hits
   M0   1.001299   3047.888621   2675.306265            0                   0
  M1a   1.002760   5253.227295   2958.902284            0                   0
  M1b   1.002720   5323.508076   3174.874444            0                   0
  M1c   1.002834   4975.490444   3244.725257            0                   0
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
  M1a             sleep     <6h  360  0.261111 0.152778 0.233333        True
  M1a             sleep    7-8h 1314  0.103501 0.109589 0.143075        True
  M1a             sleep    8-9h 1479  0.091278 0.102096 0.132522        True
  M1a             sleep    >=9h  943  0.166490 0.107105 0.151697        True
  M1a           alcohol    none 1155  0.154113 0.115152 0.152381        True
  M1b             sleep     <6h  360  0.261111 0.155556 0.230556        True
  M1b             sleep    6-7h  561  0.169340 0.103387 0.153298        True
  M1b             sleep    8-9h 1479  0.091278 0.097363 0.127113        True
   M2             sleep    8-9h 1479  0.091278 0.091954 0.121028        True
```

## 2. Posterior predictive checks: survey clusters

About 3 of 30 clusters fall outside by chance. ppp_sd near 0 means the model under-predicts how much the rate varies between clusters.

```
model  clusters_outside_90  n_clusters  observed_sd  replicated_sd_mean  ppp_sd
   M0                    3          30     0.035097            0.034670   0.464
  M1a                    2          30     0.035097            0.034948   0.464
  M1b                    2          30     0.035097            0.036358   0.601
  M1c                    2          30     0.035097            0.035621   0.539
   M2                    0          30     0.035097            0.037693   0.697
```

## 3. PSIS-LOO

Pareto k > 0.7 would make LOO unreliable.

```
   model     elpd_loo        se     p_loo  max_pareto_k  n_pareto_k_gt_0.7
      M0 -1706.761737 42.260350  3.818800      0.157449                0.0
     M1a -1663.770494 42.312498 10.411020      0.287596                0.0
     M1b -1649.142432 42.118196 10.120221      0.250481                0.0
     M1c -1640.851160 42.079715 11.202851      0.277898                0.0
      M2 -1641.157959 42.102690 17.089912      0.274873                0.0
baseline -1822.308999       NaN       NaN           NaN                NaN
```

## 3. LOO predictive metrics

Out-of-sample AUC, Brier score vs. null rate, and logistic calibration intercept (target 0) and slope (target 1).

```
   model   auc  brier  brier_null  cal_intercept  cal_slope
      M0 0.691  0.110       0.115         -0.014      0.991
     M1a 0.714  0.107       0.115         -0.030      0.981
     M1b 0.725  0.106       0.115         -0.029      0.983
     M1c 0.729  0.105       0.115         -0.033      0.980
      M2 0.729  0.105       0.115         -0.038      0.978
baseline 0.000  0.115       0.115     -30840.283 -16406.040
```

## 3. Pairwise elpd differences

Clear when |elpd_diff| > 4 and > 2 SE. M1 - M0: do habits help? M2 - M1: do clusters help?

```
   comparison  elpd_diff        se  clear
M0 - baseline 115.547263 14.616856   True
     M1c - M0  65.910576 12.289321   True
    M1c - M1a  22.919333  7.533874   True
    M1c - M1b   8.291271  4.496853  False
    M1b - M1a  14.628062  8.735790  False
     M2 - M1c  -0.306799  1.143368  False
```

## 3. az.compare



```
model  rank  elpd_diff  dse  p_worse       diag_diff  diag_elpd    p    elpd   se  weight
  M1c     0        0.0  0.0      NaN             NaN        NaN 11.2 -1640.0 42.0    0.60
   M2     1       -0.0  1.1     0.61 |elpd_diff| < 4        NaN 17.1 -1640.0 42.0    0.28
  M1b     2       -8.0  4.5     0.97             NaN        NaN 10.1 -1650.0 42.0    0.08
  M1a     3      -20.0  7.5     1.00             NaN        NaN 10.4 -1660.0 42.0    0.03
   M0     4      -70.0 12.0     1.00             NaN        NaN  3.8 -1710.0 42.0    0.01
```

## 4. Prior sensitivity: posterior means by prior scale

Shifts above about 0.5 posterior SD are worth discussing.

```
model                term    0.5    1.0    2.0  max_abs_shift_in_sd
   M0           Intercept -2.235 -2.260 -2.267                0.340
   M0               age_z -0.336 -0.343 -0.346                0.170
   M0       gender_female  0.358  0.393  0.403                0.392
   M0            income_z -0.486 -0.496 -0.499                0.222
  M1a           Intercept -2.180 -2.225 -2.239                0.429
  M1a               age_z -0.420 -0.443 -0.448                0.472
  M1a           alcohol_z  0.103  0.103  0.103                0.007
  M1a       gender_female  0.404  0.449  0.462                0.480
  M1a            income_z -0.461 -0.463 -0.462                0.037
  M1a         sedentary_z  0.182  0.184  0.184                0.045
  M1a             sleep_c -0.099 -0.100 -0.100                0.033
  M1a     smoking_current  0.470  0.547  0.573                0.651
  M1a      smoking_former  0.073  0.115  0.128                0.363
  M1a        vigorous_act -0.399 -0.437 -0.447                0.398
  M1b     I(sleep_c ** 2)  0.053  0.054  0.054                0.070
  M1b           Intercept -2.352 -2.401 -2.417                0.473
  M1b               age_z -0.423 -0.445 -0.453                0.450
  M1b           alcohol_z  0.096  0.096  0.097                0.020
  M1b       gender_female  0.404  0.450  0.463                0.479
  M1b            income_z -0.406 -0.406 -0.404                0.042
  M1b         sedentary_z  0.170  0.173  0.174                0.072
  M1b     smoking_current  0.470  0.551  0.578                0.682
  M1b      smoking_former  0.081  0.126  0.142                0.391
  M1b        vigorous_act -0.379 -0.414 -0.427                0.363
  M1c     I(sleep_c ** 2)  0.058  0.059  0.059                0.140
  M1c           Intercept -2.329 -2.377 -2.392                0.470
  M1c               age_z -0.441 -0.466 -0.474                0.502
  M1c           alcohol_z  0.091  0.092  0.092                0.043
  M1c       gender_female  0.410  0.459  0.472                0.517
  M1c            income_z -0.407 -0.405 -0.404                0.036
  M1c         sedentary_z  0.162  0.163  0.163                0.014
  M1c             sleep_c -0.114 -0.116 -0.117                0.069
  M1c     smoking_current  0.444  0.523  0.549                0.675
  M1c      smoking_former  0.080  0.126  0.142                0.391
  M1c        vigorous_act -0.384 -0.425 -0.437                0.416
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

## 5. Sleep nadir (hours, 89% credible interval)

Estimated minimum-risk sleep duration 7.5 - b1 / (2 * b2) for models with linear and quadratic sleep terms.

```
model  nadir_hours_q50  nadir_hours_q055  nadir_hours_q945
  M1c             8.48              8.12              8.94
   M2             8.48              8.11              8.95
```
