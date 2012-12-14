
-------------------------------------------------------------------------------

14-dec-2012

Upon running the second state over 10 to 100,000 unique samples (48 to 256,000,000 actual samples) I found that increasing the number of uniques samples from 10,000 to 100,000 make no appreciable difference to the results (it doesn't change the result in all but 2 cases to 5dp). I have therefore decided that 10,000 samples is enough to make sure that factor is not the limiting one in the overall accuracy.

Further to that I can see that N-1 on those bases cases produced results where between 11 and 29 individual outages caused problems. With most of the base cases having problems with around 18 different components.

What I would expect to see is that the base cases where there were only 13 or 14 problematic components should have a higher probability of acceptability than those with 21 or 22 problematic components. 

Actually this isn't the case. There is an appreciable change in the shape of the graph as you move up the number of failed components but this doesn't predict as strongly as I would expect if N-1 were a good predictor of overall system security.

There needs to be a proper statistical analysis of the number to see if this is confirmed analytically, especially as the change could be explained with an increase in the number of samples as you move through the graph causing the higher varience not the number of n-1 problems being a good predictor of overall system stability. 

I would like too see if N-2 is a better predictor than n-1. It would also make sense to use more than 100 base cases. 1,000 base cases with 10,000 samples should take about 5 days to run (unless n-2 was wanted which would take a few weeks).

-------------------------------------------------------------------------------

I have taken the three area reliability test system (RTS) and sampled it to try and find an estimate for the probability that the system will remain acceptable for an hour without emergency operator action. 

From the RTS I have used:

- System bus load as a percentage of the peak based upon hour of day and day of year.
- Line, and generating unit failure probabilities and repair times.
- Correlated failures line on common right of way and common structure.

I have added busbar failure rates of 0.025 and a mean time to repair of 13h from the literature.

-------------------------------------------------------------------------------