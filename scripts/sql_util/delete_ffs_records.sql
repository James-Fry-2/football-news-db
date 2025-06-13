-- Soft delete Fantasy Football Scout records from today only
-- This will mark articles with source = 'Fantasy Football Scout' created today as deleted

-- First, show count of records to be soft deleted from today
SELECT 
    COUNT(*) as total_ffs_articles_today,
    MIN(created_at) as oldest_article_today,
    MAX(created_at) as newest_article_today
FROM article 
WHERE source = 'Fantasy Football Scout' 
AND is_deleted = false
AND DATE(created_at) = CURRENT_DATE;

-- Show some sample records that will be soft deleted
SELECT 
    id,
    title,
    url,
    published_date,
    created_at,
    is_deleted
FROM article 
WHERE source = 'Fantasy Football Scout' 
AND is_deleted = false
AND DATE(created_at) = CURRENT_DATE
ORDER BY created_at DESC
LIMIT 10;

-- Soft delete Fantasy Football Scout articles created today only
-- This sets is_deleted = true and deleted_at = current timestamp
UPDATE article 
SET 
    is_deleted = true,
    deleted_at = NOW(),
    updated_at = NOW()
WHERE source = 'Fantasy Football Scout'
AND is_deleted = false
AND DATE(created_at) = CURRENT_DATE;

-- Show confirmation of soft deletion
SELECT 
    COUNT(CASE WHEN is_deleted = false THEN 1 END) as remaining_active_ffs_articles_today,
    COUNT(CASE WHEN is_deleted = true THEN 1 END) as soft_deleted_ffs_articles_today
FROM article 
WHERE source = 'Fantasy Football Scout' 
AND DATE(created_at) = CURRENT_DATE; 