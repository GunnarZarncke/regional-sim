# Finance and markets — scope refuse

This regional household book is not a bank-run or market simulator. Quantitative withdrawal calibration and global-market calibration are **refused**, not postponed pending metadata.

## What the book contains

- One household deposit per participant, assigned to one of two fictional banks, lognormal balances clipped to **$200–$120,000** (`engine.py`). That is below the FDIC standard coverage of **$250,000 per depositor, per insured bank, per ownership category**. Every household account is fully insured retail under a single-ownership reading.
- Retailer and institutional deposits of tens of millions of dollars. Those sit above the insurance cap but are not participants who choose to withdraw. Weekly payroll and prepaid restock fail with `unpaid_payroll` / `procurement_finance_delays` if the payer's balance is short. Ordinary runs do not exhaust the $20,000,000 retailer endowment. Firms do not borrow, fail, or close.
- Payment delay: electronic decline when the payments factor is low; settlement retry when power cuts bank access (`power_to_payments`). Conservation of deposits, cash, and escrow.

## What is not fitted

- Silicon Valley Bank, Signature Bank, and First Republic Bank withdrawal **rates** from the FDIC staff study *Dissecting Depositor Flight* (2026). The study's qualitative ordering (fully insured retail generally did not run; uninsured and large depositors were more likely to) does not transfer as a Columbus hazard. https://www.fdic.gov/news/press-releases/2026/fdic-releases-staff-study-deposit-flows-three-failed-banks-spring-2023
- Basel LCR 30-calendar-day runoff weights as minute-by-minute withdrawal probabilities. https://www.bis.org/committees/bcbs/basel-framework/standard/lcr?allChapters=true
- Global markets, exchanges, or order-book price discovery. Those domains are absent. Adding them would be a new model, not a calibration of this one.

Extra account metadata would not create uninsured or large-depositor groups while household balances stay under $250,000, and would still not supply a matched pre-failure flow panel.

Payment-system stress and household insufficient-funds remain as implemented. They are not a depositor-run calibration.
