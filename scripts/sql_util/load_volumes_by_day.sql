-- Article load volumes separated by day
-- This query shows daily statistics for article uploads and processing

-- Daily article counts for the last 30 days
SELECT 
    DATE(created_at) as upload_date,
    COUNT(*) as total_articles,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_articles,
    COUNT(CASE WHEN status = 'archived' THEN 1 END) as archived_articles,
    COUNT(CASE WHEN status = 'draft' THEN 1 END) as draft_articles,
    COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) as processed_articles,
    COUNT(CASE WHEN embedding_status = 'pending' THEN 1 END) as pending_processing,
    COUNT(CASE WHEN embedding_status = 'failed' THEN 1 END) as failed_processing,
    COUNT(DISTINCT source) as unique_sources,
    ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment,
    MIN(created_at) as first_upload_time,
    MAX(created_at) as last_upload_time
FROM article 
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
    AND is_deleted = false
GROUP BY DATE(created_at)
ORDER BY upload_date DESC;

-- Weekly summary for the last 8 weeks
SELECT 
    DATE_TRUNC('week', created_at)::date as week_start,
    COUNT(*) as total_articles,
    COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) as processed_articles,
    ROUND((COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) * 100.0 / COUNT(*))::numeric, 1) as processing_rate_percent,
    COUNT(DISTINCT source) as unique_sources,
    ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment
FROM article 
WHERE created_at >= CURRENT_DATE - INTERVAL '8 weeks'
    AND is_deleted = false
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week_start DESC;

-- Monthly summary for the last 6 months
SELECT 
    DATE_TRUNC('month', created_at)::date as month_start,
    TO_CHAR(DATE_TRUNC('month', created_at), 'YYYY-MM') as month,
    COUNT(*) as total_articles,
    COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) as processed_articles,
    ROUND((COUNT(CASE WHEN embedding_status = 'completed' THEN 1 END) * 100.0 / COUNT(*))::numeric, 1) as processing_rate_percent,
    COUNT(DISTINCT source) as unique_sources,
    ROUND(AVG(sentiment_score)::numeric, 3) as avg_sentiment
FROM article 
WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
    AND is_deleted = false
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month_start DESC; 