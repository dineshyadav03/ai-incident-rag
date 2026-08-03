# Air Canada chatbot hallucinates bereavement-fare policy, tribunal finds airline liable

**Company:** Air Canada
**Category:** rag_failure
**Date:** 2024-02-14
**Source:** https://www.forbes.com/sites/marisagarcia/2024/02/19/what-air-canada-lost-in-remarkable-lying-ai-chatbot-case/

## What happened

A customer used Air Canada's website chatbot to ask about bereavement fares shortly after his grandmother's death. The chatbot told him he could "apply for bereavement fares retroactively" and submit the request "within 90 days of the date your ticket was issued." Air Canada's actual policy prohibited retroactive bereavement-fare refunds — the chatbot's answer was fabricated and contradicted the airline's own published policy.

The customer relied on the chatbot's answer, booked full-fare tickets, and was later denied the retroactive refund. He took the case to the British Columbia Civil Resolution Tribunal.

## Root cause

This is a retrieval/grounding failure: whatever system generated the chatbot's answer either retrieved the wrong policy content, failed to retrieve the correct policy at all, or generated a plausible-sounding answer not actually grounded in Air Canada's real bereavement policy. The tribunal decision doesn't give Air Canada's internal technical post-mortem, but the pattern — a support chatbot confidently stating a specific, wrong, detailed policy — matches the classic RAG failure mode of the generator filling a retrieval gap with a fluent but ungrounded answer.

Air Canada's legal defense effectively admitted there was no verification layer between the chatbot's output and the company's actual policy: it argued the chatbot was "a separate legal entity" not responsible for its own statements. Tribunal member Christopher C. Rivers rejected this as "a remarkable submission," ruling: "It should be obvious to Air Canada that it is responsible for all the information on its website," whether it comes from a static page or a chatbot.

## Fix / lessons

The tribunal awarded the customer CAD $812.02 (the bereavement fare difference plus costs). Air Canada also argued the customer should have cross-checked the chatbot's answer against the airline's own policy page — a position the tribunal also dismissed, since the entire point of a support chatbot is to save the customer that step.

The case is now widely cited as the reference example for why customer-facing generative systems need answer verification against a source of truth (exactly the citation-grounding + refusal behavior this project is built around) rather than trusting fluent generated text as if it were policy.
