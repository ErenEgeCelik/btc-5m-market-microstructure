# Market and historical settlement

The pricing study uses May–June 2026 records; the later mechanics/policy programme uses June–July
2026 recordings of BTC five-minute up/down contracts. The research
modeled settlement as a comparison of reference observations at the window boundaries. A complementary
Up/Down pair pays a total of one dollar on resolution. The exact historical tie convention should be
read from the individual contract rule; a continuous diffusion assigns zero probability to an exact tie.

Keep three quantities separate: the contractual reference, the external exchange feed used in an
estimator, and the contract's observed book prices. A basis difference between a feed and the reference
is not itself a tradeable mispricing. The pricing study's feed-self anchor and the contract's resolution
anchor have different roles.

Prices are dollars per share in [0,1]; one tick in the quoted study is one cent. Time to expiry is in
seconds. Estimator results explicitly distinguish cents per share, per decision moment and per slot.
Do not compare those denominators without the associated exposure and event counts.

The maker model selects executable prices from the book; fair-value models supply timing or direction.
Fees and rebates in the reference accounting are historical model assumptions, not a current venue
fee schedule. The repository does not automatically fetch or trade current contracts.

The study's author reports that the venue subsequently changed its settlement averaging rule. This
repository makes no dated claim about that transition and does not apply point-settlement estimates
to an averaged payoff. An archived contract-rule snapshot remains a documentation limitation for
independent verification of the original instrument specification.
