1. page 185-258: I cross-checked few numbers and I think they are aggregated positions per stock 
across all accounts. For example, market value of Accelrys Inc is 1,099,380.00 and this is identical
 to market value of Accelrys Inc in Portfolio 6DG. Likewise, I checked Abaxis Inc and I think the
  market values across different accounts that are identified add up to this number. Could you check
   one or two more cases to confirm this? If it is just the aggregate, you don't need to scrape them.

2. page 323: You can just use D. AccountName provides information that clarifies this notation, so I 
think it is fine to just scrape what is written in the pdf. --- do by hand

3. page 37-41: In this case, I would just divided the total market value by the weight based on the 
book value. For example, FIDELITY - FIXED INCOME would have 243M/265M*273M. This is of course not a 
correct estimate, but given that the account is only reporting some funds that cannot be really 
identified, the detailed information may not be as useful. We just need this entry to have correct 
total value of the account. --- do by hand

enter page 10 by hand


QUESTIONS
 10     manual enter
Ohio_STR;12/31/2007;S&P FUTURES INDEX 03/08;CD:SP08H0;-2,219,862,300.00;FUTURES EXPOSURE;-6,011;LQR-CONTRA ASSETS;LQR-CONTRA;0
 37- 41 no shares
259-311 no market value (yet there are total values) - leave missing
312-319 no shares
323     bad instrument
324-328 no shares
331-333 no shares

after RE-REIT
Ohio_STR;12/31/2007;BLACKROCK GRANITE PROP FUND;RBLKRK;160,859,492.00;D;;REAL ESTATE DOMESTIC;RE-DOM;0
Ohio_STR;12/31/2007;DDR RETAIL/MANATEE;RDDRMA;191,792,082.00;D;;REAL ESTATE DOMESTIC;RE-DOM;0
Ohio_STR;12/31/2007;REGENCY RETAIL PARTNERS LP;RRPART;13,877,722.53;D;;REAL ESTATE DOMESTIC;RE-DOM;0
MARKET VALUE on WESDOME GOLD MINES CONV is ''