-- Get the 5 most recent articles
-- This query displays the latest 5 articles ordered by creation time

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
    END as sentiment_score,
    url
FROM article 
WHERE is_deleted = false
ORDER BY created_at DESC
LIMIT 5; 