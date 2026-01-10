---
name: ton-wallet-integration
description: Add TON Connect wallet and payment flows to a Telegram Mini App. Use when implementing wallet connect, TON transactions, jetton or NFT transfers, payment status checks, or on-chain entitlement logic.
argument-hint: "[payment or wallet feature]"
---

# TON Wallet Integration

Use this skill when a Telegram Mini App needs TON wallet functionality.

## Discovery

Before implementing, identify:

- Existing frontend framework and state management.
- Whether `@tonconnect/ui` or another TON Connect library is already installed.
- Location of `tonconnect-manifest.json`.
- Backend endpoint that creates, verifies, or records payment intents.
- Whether payments are native TON, jettons, NFTs, or smart-contract calls.

## Workflow

1. Define the transaction.
   - Recipient address.
   - Amount and asset type.
   - Payload/comment format.
   - Expiration.
   - Idempotency key.
2. Add wallet connection.
   - Initialize TON Connect once.
   - Persist connection state through the provider recommended by the library.
   - Show connected wallet address in a compact, user-safe format.
3. Build transaction request.
   - Use smallest unit amounts.
   - Validate addresses.
   - Include a stable payload when the backend must reconcile payment.
4. Submit and track status.
   - Treat client submission as pending, not final.
   - Verify on the backend or through an indexer before granting durable entitlement.
5. Handle failure states.
   - User rejects wallet prompt.
   - Wallet unavailable.
   - Transaction expires.
   - Chain confirmation delayed.
   - Backend reconciliation fails.
6. Test.
   - Use testnet when possible.
   - Keep production addresses and secrets out of source.

## Security Rules

- Do not trust the frontend as proof of payment.
- Do not grant paid entitlement until the backend verifies the chain event.
- Do not hardcode private keys, mnemonics, API tokens, or production wallet secrets.
- Avoid logging full wallet payloads when they include user-identifying data.

## Expected Output

Return:

- Wallet UX flow.
- Transaction schema.
- Backend verification approach.
- Failure handling.
- Testnet or local verification steps.
