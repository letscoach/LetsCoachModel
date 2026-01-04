-- ====================================================
-- Create Test Competitions - ALL 3 TYPES
-- Ready to copy-paste into Google Cloud SQL
-- ====================================================
-- 
-- This creates 3 competitions:
--   1. Dash100 (100m sprint)
--   2. Run5K (5km run)
--   3. PenaltyShootout (penalty kicks)
-- 
-- Each with 4 participants
-- ====================================================

-- ====================================================
-- STEP 1: CLEANUP OLD DATA
-- ====================================================
DELETE FROM `main_game`.`competition_results` LIMIT 10000;
DELETE FROM `main_game`.`transactions` WHERE transaction_type = 'Prize';
UPDATE `main_game`.`competitions` SET status_id = 7, end_time = NULL;

-- ====================================================
-- STEP 2: CREATE COMPETITION #1 - DASH100 (100m Sprint)
-- ====================================================
INSERT INTO `main_game`.`competitions` (competition_type_id, status_id, group_id, start_time)
VALUES (1, 7, 3, NOW());

SET @dash100_id = LAST_INSERT_ID();

INSERT INTO `main_game`.`competition_participants` (competition_id, token) VALUES
    (@dash100_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc1'),
    (@dash100_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc10'),
    (@dash100_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc100'),
    (@dash100_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc101');


-- ====================================================
-- STEP 3: CREATE COMPETITION #2 - RUN5K (5km Run)
-- ====================================================
INSERT INTO `main_game`.`competitions` (competition_type_id, status_id, group_id, start_time)
VALUES (2, 7, 3, NOW());

SET @run5k_id = LAST_INSERT_ID();

INSERT INTO `main_game`.`competition_participants` (competition_id, token) VALUES
    (@run5k_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc102'),
    (@run5k_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc103'),
    (@run5k_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc104'),
    (@run5k_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc105');


-- ====================================================
-- STEP 4: CREATE COMPETITION #3 - PENALTY SHOOTOUT
-- ====================================================
INSERT INTO `main_game`.`competitions` (competition_type_id, status_id, group_id, start_time)
VALUES (3, 7, 3, NOW());

SET @penalty_id = LAST_INSERT_ID();

INSERT INTO `main_game`.`competition_participants` (competition_id, token) VALUES
    (@penalty_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc1'),
    (@penalty_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc100'),
    (@penalty_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc102'),
    (@penalty_id, 'a0x24291884383d3fbe2bc74ae452d42cced24a85fc104');


-- ====================================================
-- STEP 5: VERIFY ALL COMPETITIONS
-- ====================================================
SELECT 
    '🏃 DASH100' AS competition,
    @dash100_id AS competition_id,
    COUNT(cp.token) AS participants
FROM `main_game`.`competition_participants` cp
WHERE cp.competition_id = @dash100_id

UNION ALL

SELECT 
    '🏃‍♂️ RUN5K',
    @run5k_id,
    COUNT(cp.token)
FROM `main_game`.`competition_participants` cp
WHERE cp.competition_id = @run5k_id

UNION ALL

SELECT 
    '⚽ PENALTY',
    @penalty_id,
    COUNT(cp.token)
FROM `main_game`.`competition_participants` cp
WHERE cp.competition_id = @penalty_id;


-- ====================================================
-- SHOW PARTICIPANTS FOR EACH
-- ====================================================
SELECT 
    CASE 
        WHEN cp.competition_id = @dash100_id THEN 'Dash100'
        WHEN cp.competition_id = @run5k_id THEN 'Run5K'
        WHEN cp.competition_id = @penalty_id THEN 'Penalty'
    END AS competition_type,
    cp.competition_id,
    p.name AS player_name,
    cp.token
FROM `main_game`.`competition_participants` cp
LEFT JOIN `main_game`.`players` p ON cp.token = p.token
WHERE cp.competition_id IN (@dash100_id, @run5k_id, @penalty_id)
ORDER BY cp.competition_id, p.name;


-- ====================================================
-- DONE! NOW RUN IN PYTHON:
-- ====================================================
-- 
-- cd c:\Users\gideo\Documents\GitHub\LetsCoachModel2
-- 
-- python test_full_competition_flow.py
--   Choose 1 (Dash100) and enter the dash100_id shown above
-- 
-- python test_full_competition_flow.py
--   Choose 2 (Run5K) and enter the run5k_id shown above
-- 
-- python test_full_competition_flow.py
--   Choose 3 (Penalty) and enter the penalty_id shown above
--
-- ====================================================
