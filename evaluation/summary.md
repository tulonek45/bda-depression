# Model evaluation

## 1. Convergence

Targets: R-hat <= 1.01, ESS >= 400, no divergences or max tree depth hits.

```
model  max_r_hat  min_ess_bulk  min_ess_tail  divergences  max_treedepth_hits
   M0   1.001299   3047.888621   2675.306265            0                   0
  M1a   1.002760   5253.227295   2958.902284            0                   0
  M1b   1.002185   5250.257856   2828.412430            0                   0
  M1c   1.003066   4973.243132   2785.836778            0                   0
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
  M1b             sleep     <6h  360  0.261111 0.158333 0.230556        True
  M1b             sleep    6-7h  561  0.169340 0.103387 0.151515        True
  M1b             sleep    8-9h 1479  0.091278 0.096687 0.127789        True
   M2             sleep    8-9h 1479  0.091278 0.091954 0.121028        True
```

## 2. Posterior predictive checks: survey clusters

About 3 of 30 clusters fall outside by chance. ppp_sd near 0 means the model under-predicts how much the rate varies between clusters.

```
model  clusters_outside_90  n_clusters  observed_sd  replicated_sd_mean  ppp_sd
   M0                    3          30     0.035097            0.034670   0.464
  M1a                    2          30     0.035097            0.034948   0.464
  M1b                    2          30     0.035097            0.036335   0.600
  M1c                    2          30     0.035097            0.035794   0.545
   M2                    0          30     0.035097            0.037693   0.697
```

## 3. PSIS-LOO

Pareto k > 0.7 would make LOO unreliable.

```
   model     elpd_loo        se     p_loo  max_pareto_k  n_pareto_k_gt_0.7
      M0 -1706.761737 42.260350  3.818800      0.157449                0.0
     M1a -1663.770494 42.312498 10.411020      0.287596                0.0
     M1b -1649.184557 42.122884 10.169443      0.234929                0.0
     M1c -1640.905373 42.105196 11.267363      0.250048                0.0
      M2 -1641.157959 42.102690 17.089912      0.274873                0.0
baseline -1822.308999       NaN       NaN           NaN                NaN
```

## 3. Pairwise elpd differences

Clear when |elpd_diff| > 4 and > 2 SE. M1 - M0: do habits help? M2 - M1: do clusters help?

```
   comparison  elpd_diff        se  clear
M0 - baseline 115.547263 14.616856   True
     M1a - M0  42.991243 10.310509   True
    M1b - M1a  14.585936  8.775360  False
    M1c - M1b   8.279184  4.507538  False
     M2 - M1c  -0.252586  1.145000  False
```

## 3. az.compare



```
model  rank  elpd_diff  dse  p_worse       diag_diff  diag_elpd    p    elpd   se  weight
  M1c     0        0.0  0.0      NaN             NaN        NaN 11.3 -1640.0 42.0    0.56
   M2     1       -0.0  1.1     0.59 |elpd_diff| < 4        NaN 17.1 -1640.0 42.0    0.31
  M1b     2       -8.0  4.5     0.97             NaN        NaN 10.2 -1650.0 42.0    0.08
  M1a     3      -20.0  7.6     1.00             NaN        NaN 10.4 -1660.0 42.0    0.04
   M0     4      -70.0 12.0     1.00             NaN        NaN  3.8 -1710.0 42.0    0.01
```

## 4. Prior sensitivity: posterior means by prior scale

Shifts above about 0.5 posterior SD are worth discussing.

```
model                term    0.5    1.0    2.0  max_abs_shift_in_sd
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
  M1b     I(sleep_c ** 2)  0.054  0.054  0.054                0.048
  M1b           Intercept -2.356 -2.402 -2.417                0.423
  M1b               age_z -0.422 -0.445 -0.453                0.468
  M1b           alcohol_z  0.095  0.096  0.096                0.029
  M1b       gender_female  0.405  0.451  0.464                0.465
  M1b            income_z -0.405 -0.404 -0.404                0.012
  M1b         sedentary_z  0.170  0.173  0.173                0.078
  M1b     smoking_current  0.469  0.554  0.580                0.723
  M1b      smoking_former  0.081  0.125  0.139                0.387
  M1b        vigorous_act -0.379 -0.416 -0.427                0.378
  M1c     I(sleep_c ** 2)  0.059  0.059  0.059                0.016
  M1c           Intercept -2.332 -2.380 -2.391                0.468
  M1c               age_z -0.442 -0.467 -0.472                0.507
  M1c           alcohol_z  0.091  0.092  0.092                0.025
  M1c       gender_female  0.411  0.461  0.471                0.521
  M1c            income_z -0.406 -0.405 -0.405                0.025
  M1c         sedentary_z  0.161  0.163  0.164                0.045
  M1c             sleep_c -0.115 -0.117 -0.117                0.052
  M1c     smoking_current  0.440  0.524  0.546                0.692
  M1c      smoking_former  0.081  0.127  0.138                0.391
  M1c        vigorous_act -0.386 -0.426 -0.436                0.412
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
