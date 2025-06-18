-- General purpose article deletion script
-- This script provides various options for deleting articles with safety checks
-- Uncomment and modify the desired DELETE section at the bottom

-- =============================================================================
-- SAFETY CHECK: Show articles that match your criteria BEFORE deleting
-- =============================================================================

-- Option 1: Delete by source
SELECT 
    source,
    COUNT(*) as total_articles,
    MIN(created_at) as oldest_article,
    MAX(created_at) as newest_article
FROM article 
WHERE source = 'BBC Sport' 
AND DATE(created_at) >= '2025-06-16'
AND is_deleted = false
GROUP BY source;

-- Option 2: Delete by date range
-- SELECT 
--     COUNT(*) as total_articles,
--     source,
--     MIN(created_at) as oldest_article,
--     MAX(created_at) as newest_article
-- FROM article 
-- WHERE DATE(created_at) BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
-- AND is_deleted = false
-- GROUP BY source
-- ORDER BY total_articles DESC;

-- Option 3: Delete by specific date
-- SELECT 
--     COUNT(*) as total_articles,
--     source,
--     MIN(created_at) as oldest_article,
--     MAX(created_at) as newest_article
-- FROM article 
-- WHERE DATE(created_at) = 'YYYY-MM-DD'
-- AND is_deleted = false
-- GROUP BY source
-- ORDER BY total_articles DESC;

-- Option 4: Delete by ID range
-- SELECT 
--     COUNT(*) as total_articles,
--     MIN(id) as min_id,
--     MAX(id) as max_id,
--     MIN(created_at) as oldest_article,
--     MAX(created_at) as newest_article
-- FROM article 
-- WHERE id BETWEEN 100 AND 200
-- AND is_deleted = false;

-- Option 5: Delete by multiple criteria (source + date)
-- SELECT 
--     COUNT(*) as total_articles,
--     MIN(created_at) as oldest_article,
--     MAX(created_at) as newest_article
-- FROM article 
-- WHERE source = 'YOUR_SOURCE_NAME'
-- AND DATE(created_at) = 'YYYY-MM-DD'
-- AND is_deleted = false;

-- =============================================================================
-- PREVIEW: Show sample records that will be deleted
-- =============================================================================

-- Uncomment one of these to see sample records before deletion:

-- Preview by source:
-- SELECT 
--     id,
--     title,
--     source,
--     url,
--     published_date,
--     created_at,
--     is_deleted
-- FROM article 
-- WHERE source = 'YOUR_SOURCE_NAME'
-- AND is_deleted = false
-- ORDER BY created_at DESC
-- LIMIT 10;

-- Preview by date:
-- SELECT 
--     id,
--     title,
--     source,
--     url,
--     published_date,
--     created_at,
--     is_deleted
-- FROM article 
-- WHERE DATE(created_at) = 'YYYY-MM-DD'
-- AND is_deleted = false
-- ORDER BY created_at DESC
-- LIMIT 10;

-- =============================================================================
-- DELETION OPTIONS: Uncomment ONE of these sections to perform deletion
-- =============================================================================

-- OPTION 1: SOFT DELETE by source
-- UPDATE article 
-- SET 
--     is_deleted = true,
--     deleted_at = NOW(),
--     updated_at = NOW()
-- WHERE source = 'BBC Sport' 
-- AND DATE(created_at) >= '2025-06-16'
-- AND is_deleted = false;

-- DELETE FROM article 
-- WHERE source = 'BBC Sport' 
-- AND DATE(created_at) >= '2025-06-16'
-- AND is_deleted = true;


-- OPTION 2: SOFT DELETE by date range
-- UPDATE article 
-- SET 
--     is_deleted = true,
--     deleted_at = NOW(),
--     updated_at = NOW()
-- WHERE DATE(created_at) BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'
-- AND is_deleted = false;

-- OPTION 3: SOFT DELETE by specific date
-- UPDATE article 
-- SET 
--     is_deleted = true,
--     deleted_at = NOW(),
--     updated_at = NOW()
-- WHERE DATE(created_at) = 'YYYY-MM-DD'
-- AND is_deleted = false;

-- OPTION 4: SOFT DELETE by ID range
-- UPDATE article 
-- SET 
--     is_deleted = true,
--     deleted_at = NOW(),
--     updated_at = NOW()
-- WHERE id BETWEEN 100 AND 200
-- AND is_deleted = false;

-- OPTION 5: SOFT DELETE by source AND date
-- UPDATE article 
-- SET 
--     is_deleted = true,
--     deleted_at = NOW(),
--     updated_at = NOW()
-- WHERE source = 'YOUR_SOURCE_NAME'
-- AND DATE(created_at) = 'YYYY-MM-DD'
-- AND is_deleted = false;

-- OPTION 6: HARD DELETE by source (PERMANENT - USE WITH CAUTION!)
-- DELETE FROM article 
-- WHERE source = 'YOUR_SOURCE_NAME'
-- AND is_deleted = false;

-- OPTION 7: HARD DELETE by date (PERMANENT - USE WITH CAUTION!)
-- DELETE FROM article 
-- WHERE DATE(created_at) = 'YYYY-MM-DD'
-- AND is_deleted = false;

-- OPTION 8: HARD DELETE by ID range (PERMANENT - USE WITH CAUTION!)
-- DELETE FROM article 
-- WHERE id BETWEEN 100 AND 200
-- AND is_deleted = false;

-- =============================================================================
-- CONFIRMATION: Check results after deletion
-- =============================================================================

-- After running deletion, uncomment this to confirm:
-- SELECT 
--     COUNT(CASE WHEN is_deleted = false THEN 1 END) as remaining_active_articles,
--     COUNT(CASE WHEN is_deleted = true THEN 1 END) as soft_deleted_articles,
--     COUNT(*) as total_articles
-- FROM article;

-- Check specific source after deletion:
-- SELECT 
--     source,
--     COUNT(CASE WHEN is_deleted = false THEN 1 END) as active_articles,
--     COUNT(CASE WHEN is_deleted = true THEN 1 END) as deleted_articles
-- FROM article 
-- GROUP BY source
-- ORDER BY active_articles DESC; 