-- Show articles uploaded today
-- This query displays articles that were created today (based on created_at timestamp)

SELECT 
    id,
    title,
    source,
    author,
    published_date,
    created_at,
    status,
    embedding_status,
    CASE 
        WHEN sentiment_score IS NOT NULL THEN ROUND(sentiment_score::numeric, 3)
        ELSE NULL 
    END as sentiment_score
FROM article 
WHERE DATE(created_at) = CURRENT_DATE-1
    AND is_deleted = false
ORDER BY created_at DESC;

-- Summary count
SELECT 
    COUNT(*) as total_articles_today,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_articles,
    COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) as processed_articles,
    ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment
FROM article 
WHERE DATE(created_at) = CURRENT_DATE
    AND is_deleted = false; 