-- ====================================================
-- Cleanup Test Competition Data
-- ====================================================
-- 
-- Use this script to clean up test competition data
-- before running new tests
--
-- WARNING: This will delete competition results and prizes!
-- ====================================================

-- Show what will be deleted
SELECT 
    'Competition Results' AS table_name,
    COUNT(*) AS rows_to_delete
FROM `main_game`.`competition_results`
UNION ALL
SELECT 
    'Prize Transactions',
    COUNT(*)
FROM `main_game`.`transactions`
WHERE transaction_type = 'Prize';

-- Delete competition results
DELETE FROM `main_game`.`competition_results` 
LIMIT 10000;

-- Reset competitions to "ready" status (status_id = 14)
UPDATE `main_game`.`competitions` 
SET status_id = 14, 
    end_time = NULL;

-- Delete prize transactions
DELETE FROM `main_game`.`transactions` 
WHERE transaction_type = 'Prize';

-- Verify cleanup
SELECT 
    'After Cleanup - Competition Results' AS info,
    COUNT(*) AS remaining_rows
FROM `main_game`.`competition_results`
UNION ALL
SELECT 
    'After Cleanup - Prize Transactions',
    COUNT(*)
FROM `main_game`.`transactions`
WHERE transaction_type = 'Prize';

SELECT 'Cleanup completed!' AS status;
