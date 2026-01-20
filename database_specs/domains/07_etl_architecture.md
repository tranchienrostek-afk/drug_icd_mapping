# ETL Architecture & Concurrency Strategy

## Overview
The ETL (Extract, Transform, Load) service manages the ingestion of large CSV datasets into the `knowledge_base`. Given the SQLite database backend, handling concurrency between long-running ETL processes (Writes) and real-time API queries (Reads) is critical to prevent `database is locked` errors.

## Core Problems Solved
1. **Readers Blocking Writers (and vice versa):** In standard SQLite (DELETE journal mode), a Write transaction locks the file, blocking all Readers.
2. **Interleaved Read/Write Deadlocks:** The original ETL process iterated through rows, performing a matching lookup (Read) and then an Insert/Update (Write) for each row.
   - Row 1: Acquires Write Lock (Insert).
   - Row 2: Tries to open new connection for Lookup (Read).
   - **Result:** Deadlock/Timeout because Row 2's Read is blocked by Row 1's active Write transaction.

## Architecture Solution

### 1. Pre-Lookup Strategy (Read-Then-Write)
We completely separated the Read phase from the Write phase.

**Phase A: Read (Pre-lookup)**
- Parse the entire CSV in memory.
- Extract unique drug names.
- Perform batch matching using `DrugSearchService` (Async).
- **Benefit:** No database Write transaction is open during this phase. Lookups are fast and non-blocking.

**Phase B: Write (Batch Insert)**
- Open a *single* database connection.
- Enable `WAL` (Write-Ahead Logging) mode.
- Iterate through rows, using the in-memory matched results from Phase A.
- Perform Inserts/Updates within a single transaction (or batched transactions).
- **Benefit:** The Write lock is held only during the actual insertion, not during the slow matched logic.

### 2. WAL Mode (Write-Ahead Logging)
We explicitly enable `PRAGMA journal_mode=WAL;` for the ETL connection to allow higher concurrency, although the Pre-lookup strategy is the primary defense against locking.

### 3. Async Wrapper via `asyncio.run`
Since `DrugSearchService` is async (using AI/Vector search) but `process_raw_log` runs in a background thread (Sync), we use:
```python
# Create a single event loop for the entire batch lookup
batch_map = asyncio.run(batch_lookup_drugs(unique_drugs))
```
This is efficient and avoids creating an event loop per row.

## Data Flow Diagram
```mermaid
graph TD
    A[Upload CSV] --> B[Parse Stats]
    B --> C{Extract Unique Drugs}
    C --> D[Async Batch Lookup]
    D --> E[(Vector DB / FTS)]
    E -- Matches --> D
    D -- Drug Map --> F[Open DB (WAL)]
    F --> G[Iterate Rows]
    G -- Use Map --> H[Insert/Update KB]
    H --> I[Commit Transaction]
```

## Error Handling
- **Row-level Errors:** Individual row failures (formatting) are logged but do not stop the batch.
- **Batch-level Errors:** Fatal errors catch exception, log trace, and mark batch as failed.
- **Logging:** All raw data is logged via `log_raw_data` (Async, awaited) before processing starts.
